from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor

import Start.Functions
import TermsAndConditions.Functions
from APIs.APIsSingleton import APIsSingleton
from Configurations.BotConfig import BOT_TOKEN
from Configurations.StringConstants import INSERT_PAGE
from Gaming.Flash import create_flash_path
from Gaming.Functions import create_event_keyboard, place_bet
from Gaming.Pool import open_pool, open_pool_cbq
from TelegramAssets.About import open_about
# from Search.Functions import search
from TelegramAssets.InlineNumericKeyboard import *
from TelegramAssets.TelegramPager import create_pager, open_page, insert_page
from TermsAndConditions.Constants import *
from Utils.StringShortener import StringShortener
from Utils.Validators import is_external_address_request
from Wallet.Functions import view_wallet, switch_wallet, select_active_wallet_type, deposit, generate_qr_code, \
    set_withdrawal, insert_external_address, confirm_withdrawal

# Endpoint you are trying to call

# Bot token from @BotFather


# Initializing bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
local_storage = LocalStorage.get_instance()
dp = Dispatcher(bot, storage=storage)
ss = StringShortener()
APIs_singleton = APIsSingleton.get_instance()
champions_api = APIs_singleton.get_champions_api()


# async def inline_query_search(inline_query: types.InlineQuery):
#     await search(bot, champions_api, inline_query)


# TODO Uncomment to allow search
# dp.register_inline_handler(inline_query_search)
@dp.callback_query_handler(lambda query: query.data == "open_pool")
async def request_pool(callback_query: types.CallbackQuery):
    await open_pool_cbq(callback_query)

@dp.message_handler(commands=['pool'])
async def request_open_pool(message: types.Message):
    await open_pool(message)

@dp.callback_query_handler(lambda query: query.data == "my_bets")
async def request_deposit(callback_query: types.CallbackQuery, state: FSMContext):
    await deposit(callback_query, state)

@dp.callback_query_handler(lambda query: query.data.startswith('about$'))
async def request_about(callback_query: types.CallbackQuery):
    params = extract_callback_data(callback_query.data)
    page = params[0]
    await open_about(callback_query, page)

@dp.callback_query_handler(lambda query: query.data.startswith('confirm_withdrawal$'))
async def request_confirm_withdrawal(callback_query: types.CallbackQuery):
    params = extract_callback_data(callback_query.data)
    cid = params[0]
    await confirm_withdrawal(callback_query, cid)


@dp.message_handler(lambda message: message.reply_to_message is not None and
                                    is_external_address_request(message.reply_to_message.text))
async def request_insert_external_address(message: types.Message):
    await insert_external_address(message, bot)


@dp.callback_query_handler(lambda query: query.data.startswith('set_withdrawal$'))
async def request_set_withdrawal(callback_query: types.CallbackQuery, state: FSMContext):
    params = extract_callback_data(callback_query.data)
    method = params[0]
    wallet_type = params[1]
    await set_withdrawal(callback_query,
                         method, wallet_type, state)


@dp.callback_query_handler(lambda query: query.data.startswith('place_bet$'))
async def request_place_bet(callback_query: types.CallbackQuery, state: FSMContext):
    params = extract_callback_data(callback_query.data)
    place_bet_id = params[0]
    await place_bet(callback_query,
                    place_bet_id, state)


@dp.callback_query_handler(lambda query: query.data.startswith('sel_odd$'))
async def request_selected_market_key_name(callback_query: types.CallbackQuery, state: FSMContext):
    params = extract_callback_data(callback_query.data)
    event_id = ss.retrieve_original(params[0])
    sport_id = params[1]
    selected_market_key_name = ss.retrieve_original(params[2])
    odd_id = params[3]
    continue_path = params[4]

    try:
        currency = (await state.get_data())['active_wallet_type']
    except KeyError:
        currency = "DEMO"
        await state.set_data({'active_wallet_type': currency})
    if continue_path == 'default':

        await create_inline_numeric_keyboard(callback_query,
                                             f"BET#{event_id}#{sport_id}#{selected_market_key_name}#{odd_id}#{currency}",
                                             str(MessageResponseType.EDIT), state)
    elif continue_path == 'flash':
        await create_flash_path(callback_query,event_id,sport_id,selected_market_key_name,odd_id,currency)


@dp.callback_query_handler(lambda query: query.data.startswith('sel_mk$'))
async def request_selected_market_key_name(callback_query: types.CallbackQuery):
    params = extract_callback_data(callback_query.data)
    event_id = ss.retrieve_original(params[0])
    sport_id = params[1]
    event = await champions_api.get_event(sport_id, event_id)
    selected_market_key_name = ss.retrieve_original(params[2])
    await create_event_keyboard(event, sport_id, selected_market_key_name)


@dp.callback_query_handler(lambda query: query.data == "generate_qr_code")
async def request_generate_qr_code(callback_query: types.CallbackQuery, state: FSMContext):
    await generate_qr_code(callback_query, state)


# @dp.callback_query_handler(lambda query: query.data == "withdraw")
# async def request_withdraw(callback_query: types.CallbackQuery, state: FSMContext):
#     await deposit(callback_query, state)


@dp.callback_query_handler(lambda query: query.data == "deposit")
async def request_deposit(callback_query: types.CallbackQuery, state: FSMContext):
    await deposit(callback_query, state)


@dp.callback_query_handler(lambda query: query.data.startswith('select_active_wallet_type$'))
async def request_select_active_wallet_type(callback_query: types.CallbackQuery, state: FSMContext):
    params = extract_callback_data(callback_query.data)
    active_wallet_type = params[0]
    await select_active_wallet_type(callback_query, active_wallet_type, state)


@dp.callback_query_handler(lambda query: query.data == "switch_wallet")
async def request_switch_wallet(callback_query: types.CallbackQuery, state: FSMContext):
    await switch_wallet(callback_query, state)


@dp.callback_query_handler(lambda query: query.data == "view_wallet")
async def request_view_wallet(callback_query: types.CallbackQuery, state: FSMContext):
    await view_wallet(callback_query, state)


@dp.message_handler(lambda message: message.reply_to_message is not None and
                                    message.reply_to_message.text == INSERT_PAGE)
async def insert_page_reply(message: types.Message):
    await insert_page(message, bot)


@dp.callback_query_handler(lambda query: query.data.startswith('create_pager$'))
async def request_create_pager(callback_query: types.CallbackQuery):
    params = extract_callback_data(callback_query.data)
    context_id = params[0]
    selection_id = params[1]
    await create_pager(callback_query, context_id, selection_id)


@dp.callback_query_handler(lambda query: query.data.startswith('open_page$'))
async def request_open_page(callback_query: types.CallbackQuery):
    await open_page(callback_query)


@dp.callback_query_handler(lambda query: query.data.startswith('numeric_kb$'))
async def request_edit_inline_numeric_keyboard(callback_query: types.CallbackQuery):
    await put_inline_numeric_keyboard(callback_query)


@dp.callback_query_handler(lambda query: query.data.startswith('create_inline_num_kb$'))
async def request_create_inline_numeric_keyboard(callback_query: types.CallbackQuery, state: FSMContext):
    params = extract_callback_data(callback_query.data)
    context_id = params[1]
    edit = params[0] == str(MessageResponseType.EDIT)
    await create_inline_numeric_keyboard(callback_query, context_id, edit, state)


@dp.message_handler(Text(equals=TERMS_AND_CONDITIONS_AGREE, ignore_case=True))
async def approve_term_and_conditions(message: types.Message):
    await TermsAndConditions.Functions.approve_terms_and_conditions(message)


@dp.callback_query_handler(lambda query: query.data == "close")
async def request_generate_qr_code(callback_query: types.CallbackQuery):
    await callback_query.message.delete()


@dp.message_handler(commands=['wallet', 'balance'])
async def balance_handler(message: types.Message):
    await Start.Functions.show_balance(message)


@dp.callback_query_handler(lambda query: query.data == "back_to_start")
async def request_back_to_start(callback_query: types.CallbackQuery):
    await Start.Functions.back_to_start(callback_query)


@dp.message_handler(commands=['start'])
async def welcome_handler(message: types.Message):
    await Start.Functions.start_bot(message)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
