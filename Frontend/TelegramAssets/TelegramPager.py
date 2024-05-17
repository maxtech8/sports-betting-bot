from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from aiogram.utils.exceptions import MessageNotModified

from Configurations.NumericConstants import PAGER_ITEMS_PER_PAGE
from Configurations.StringConstants import PREVIOUS_BUTTON, NOOP_BUTTON, NEXT_BUTTON, START_BUTTON, END_BUTTON, \
    INSERT_PAGE, BACK_BUTTON
from Database.LocalStorage import LocalStorage
from Gaming.Functions import get_sports_list, get_leagues_list, get_events_list, view_event, get_my_bets_list, view_bet, get_top_events_list
from Utils.Convertors import function_to_bytes, bytes_to_function
from Utils.Generators import generate_id
from Utils.StringShortener import StringShortener
from Utils.TelegramUtils import extract_callback_data
from Utils.Validators import is_int

ss = StringShortener()

local_storage = LocalStorage.get_instance()


async def context_id_to_params(context_id: str, selection_id: str):
    """
    :return: items [{id:value},{id:value} .. ], on_select_function : function, text title, type_ : MessageResponseType
    """
    if context_id == '0':
        return [{str(i + 1): chr(65 + i)} for i in
                range(0, 26)], mock_on_select_function, "Test title"

    if context_id == '1':
        return [{str(i + 1): chr(65 + int(selection_id) - 1) + chr(65 + i)} for i in
                range(0, 26)], mock_on_second_select_function, "Second Page"

    if context_id == '50':
        return await get_sports_list(), on_select_sport, "🏆 *Sports* › _Leagues_ › _Events_"

    if context_id == '51':
        return await get_leagues_list(selection_id), on_select_league, "🏆 _Sports_ › *Leagues* › _Events_"

    if context_id == '52':
        return await get_events_list(selection_id), view_event, "🏆 _Sports_ › _Leagues_ › *Events*"

    if context_id == '65':
        return await get_my_bets_list(selection_id), view_bet, "📋 My Bets"

    if context_id == '150':
        return await get_top_events_list(), view_event, "⚡ Instant Bets"

async def index_items(items: list):
    dict_ = {}
    for index, value in items:
        dict_[str(index)] = value
    return dict_


async def get_markup(current_page, pager_id, total_pages, items):
    markup = InlineKeyboardMarkup()

    start_index = current_page * PAGER_ITEMS_PER_PAGE
    end_index = start_index + PAGER_ITEMS_PER_PAGE

    for resource in items[start_index:end_index]:
        (id_, val), = resource.items()
        markup.row(InlineKeyboardButton(text=val, callback_data=f'open_page${pager_id}_select_{ss.shorten(id_)}'))

    markup.row(
        InlineKeyboardButton(START_BUTTON if current_page > 0 else NOOP_BUTTON,
                             callback_data=f'open_page${pager_id}_start'),
        InlineKeyboardButton(PREVIOUS_BUTTON if current_page > 0 else NOOP_BUTTON,
                             callback_data=f'open_page${pager_id}_prev'),

        InlineKeyboardButton(f"{current_page + 1}/{max(total_pages, 1)}", callback_data=f"open_page${pager_id}_insert"),

        InlineKeyboardButton(NEXT_BUTTON if current_page < total_pages - 1 else NOOP_BUTTON,
                             callback_data=f'open_page${pager_id}_next' if current_page < total_pages - 1 else "noop"),

        InlineKeyboardButton(END_BUTTON if current_page < total_pages - 1 else NOOP_BUTTON,
                             callback_data=f'open_page${pager_id}_end' if current_page < total_pages - 1 else "noop"),
    )
    markup.row(InlineKeyboardButton(BACK_BUTTON,
                                    callback_data=f'back_to_start'))

    return markup


async def create_pager(callback_query: types.CallbackQuery, context_id, selection_id):
    items, on_select_function, pager_title = await context_id_to_params(
        context_id, selection_id)
    current_page = 0
    total_pages = -(-len(items) // PAGER_ITEMS_PER_PAGE)  # Calculate total pages
    pager_id = generate_id()

    await local_storage.post_resource(pager_id,
                                      {'items': items,
                                       "current_page": current_page,
                                       "total_pages": total_pages,
                                       "on_select_function": function_to_bytes(on_select_function)})

    markup = await get_markup(current_page, pager_id, total_pages, items)
    await callback_query.message.edit_text(text=pager_title, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)


async def open_page(callback_query: types.CallbackQuery):
    # Extracting the callback data
    params = extract_callback_data(callback_query.data)
    pager_id = params[0]
    move = params[1]

    # Assuming local_storage is an async context that retrieves data
    pager_data = await local_storage.get_resource(pager_id)

    # Extracting necessary data from the pager
    items = pager_data['items']  # Assuming 'items' is used somewhere or needed
    current_page = pager_data['current_page']
    total_pages = pager_data['total_pages']
    on_select_function = bytes_to_function(pager_data['on_select_function'])
    # mock_on_select_function(callback_query: types.CallbackQuery, selection_id: str, type_: MessageResponseType)
    if move == 'select':
        selection_id = params[-1]
        await on_select_function(callback_query, ss.retrieve_original(selection_id))
        # await local_storage.delete_resource(pager_id)
        return

    if move == 'next' and current_page < total_pages:
        new_page = current_page + 1
    elif move == 'prev' and current_page > 0:
        new_page = current_page - 1
    elif move == 'start':
        new_page = 0
    elif move == 'end':
        new_page = total_pages - 1
    elif move == 'insert':
        if callback_query.message:
            await callback_query.message.answer(text=INSERT_PAGE,
                                                reply_markup=types.ForceReply(selective=True))
            await local_storage.post_resource("insert_page_" + str(callback_query.from_user.id),
                                              {"pager_id": pager_id, "pager_chat_id": callback_query.message.chat.id,
                                               "pager_message_id": callback_query.message.message_id})
            return

    else:
        return False

    # Creating markup for inline keyboard

    markup = await get_markup(new_page, pager_id, total_pages, items)

    await callback_query.message.edit_reply_markup(reply_markup=markup)
    await local_storage.put_resource(pager_id, {"current_page": new_page})
    # markup.row(back_button_)


async def insert_page(message: types.Message, bot):
    current_page = message.text

    insert_page_data = await local_storage.get_resource("insert_page_" + str(message.from_user.id))
    pager_id = insert_page_data['pager_id']
    pager_message_id = insert_page_data['pager_message_id']
    pager_chat_id = insert_page_data['pager_chat_id']
    pager_data = await local_storage.get_resource(pager_id)

    items = pager_data['items']  # Assuming 'items' is used somewhere or needed
    total_pages = pager_data['total_pages']

    message_id = message.message_id
    reply_to_message_id = message.reply_to_message.message_id
    chat_id = message.chat.id
    reply_to_chat_id = message.reply_to_message.chat.id

    await bot.delete_message(chat_id=chat_id, message_id=message_id)
    await bot.delete_message(chat_id=reply_to_chat_id, message_id=reply_to_message_id)
    await local_storage.delete_resource("insert_page_" + str(message.from_user.id))

    if not is_int(current_page):
        await message.answer("Please insert valid number")
        return False
    current_page = int(current_page) - 1
    if current_page >= total_pages:
        current_page = total_pages - 1
    elif current_page < 0:
        current_page = 0

    await local_storage.put_resource(pager_id, {"current_page": current_page})
    markup = await get_markup(current_page, pager_id, total_pages, items)
    try:
        await bot.edit_message_reply_markup(chat_id=pager_chat_id, message_id=pager_message_id, reply_markup=markup)
    except MessageNotModified:
        pass


# ON CLICK FUNCTIONS

async def mock_on_select_function(callback_query: types.CallbackQuery, selection_id: str):
    await create_pager(callback_query, "1", selection_id)


async def mock_on_second_select_function(callback_query: types.CallbackQuery, selection_id: str):
    await callback_query.message.edit_text(f"You selected key : {selection_id}")


async def on_select_sport(callback_query: types.CallbackQuery, selection_id: str):
    await create_pager(callback_query, "51", selection_id)


async def on_select_league(callback_query: types.CallbackQuery, selection_id: str):
    await create_pager(callback_query, "52", selection_id)
