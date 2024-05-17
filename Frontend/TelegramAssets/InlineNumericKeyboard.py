from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

from Configurations.NumericConstants import CURRENCY_MAXIMUM_DIGITS
from Configurations.StringConstants import BACK_BUTTON
from Database.LocalStorage import LocalStorage
from Gaming.AmountSelector import AmountSelector
from Mock.TestFunctions import mock_keyboard_enter, mock_keyboard_cancel, mock_keyboard_string
from TelegramAssets.MessageResponseType import MessageResponseType
from Utils.Convertors import function_to_bytes, bytes_to_function
from Utils.Generators import generate_id
from Utils.TelegramUtils import extract_callback_data
from Utils.Validators import is_float
from Wallet.Functions import WithdrawKeyboardFactory

local_storage = LocalStorage.get_instance()


async def context_id_to_params(context_id: str, user_id: str):
    """
    :return: string_builder, activation_function, cancellation_function, max_number, min_number,type : send/edit
    """
    if context_id == '0':
        return mock_keyboard_string, mock_keyboard_enter, mock_keyboard_cancel, 253.4, 0, MessageResponseType.EDIT

    # Withdrawal
    if "WLT#" in context_id:
        wallet_type = context_id.split("#")[-1]
        clas = await WithdrawKeyboardFactory.get_class(wallet_type)
        balance = await clas.get_balance(
            user_id)
        if balance < await clas.get_minimum_withdraw():
            return "Not enough balance, please deposit or switch wallet", False, False, False, False, False

        elif wallet_type == 'DEMO':
            return f"You can not withdraw DEMO at the moment!", False, False, False, False, False

        return clas.withdraw_keyboard_string, clas.withdraw_keyboard_enter, clas.withdraw_keyboard_cancel, balance, await clas.get_minimum_withdraw(), MessageResponseType.EDIT

    if "BET#" in context_id:
        params = context_id.split("#")
        event_id = params[1]
        sport_id = params[2]
        selected_market_key_name = params[3]
        odd_id = params[4]
        currency = params[5]
        wlt = await WithdrawKeyboardFactory.get_class(currency)

        clas = AmountSelector(event_id, sport_id, selected_market_key_name, odd_id, currency)
        balance = await wlt.get_balance(
            user_id)
        minimum = await wlt.get_minimum_withdraw()
        if balance < minimum:
            return "Not enough balance, please deposit or switch wallet", False, False, False, False, False
        return clas.bet_amount_keyboard_string, clas.verify_bet, clas.withdraw_keyboard_cancel, balance, minimum, MessageResponseType.EDIT


async def inline_numeric_keyboard(keyboard_id: str):
    # Initialize markup
    markup = InlineKeyboardMarkup()

    # Define buttons
    zero_btn = InlineKeyboardButton("0", callback_data=f"numeric_kb$num_0_{keyboard_id}")
    one_btn = InlineKeyboardButton("1", callback_data=f"numeric_kb$num_1_{keyboard_id}")
    two_btn = InlineKeyboardButton("2", callback_data=f"numeric_kb$num_2_{keyboard_id}")
    three_btn = InlineKeyboardButton("3", callback_data=f"numeric_kb$num_3_{keyboard_id}")
    four_btn = InlineKeyboardButton("4", callback_data=f"numeric_kb$num_4_{keyboard_id}")
    five_btn = InlineKeyboardButton("5", callback_data=f"numeric_kb$num_5_{keyboard_id}")
    six_btn = InlineKeyboardButton("6", callback_data=f"numeric_kb$num_6_{keyboard_id}")
    seven_btn = InlineKeyboardButton("7", callback_data=f"numeric_kb$num_7_{keyboard_id}")
    eight_btn = InlineKeyboardButton("8", callback_data=f"numeric_kb$num_8_{keyboard_id}")
    nine_btn = InlineKeyboardButton("9", callback_data=f"numeric_kb$num_9_{keyboard_id}")
    dot_btn = InlineKeyboardButton(".", callback_data=f"numeric_kb$num_._{keyboard_id}")

    percent_10_btn = InlineKeyboardButton("10%", callback_data=f"numeric_kb$percent_10_{keyboard_id}")
    percent_25_btn = InlineKeyboardButton("25%", callback_data=f"numeric_kb$percent_25_{keyboard_id}")
    percent_50_btn = InlineKeyboardButton("50%", callback_data=f"numeric_kb$percent_50_{keyboard_id}")
    percent_100_btn = InlineKeyboardButton("100%", callback_data=f"numeric_kb$percent_100_{keyboard_id}")

    enter_btn = InlineKeyboardButton("✅ Enter", callback_data=f"numeric_kb$enter_{keyboard_id}")
    cancel_btn = InlineKeyboardButton("✖ Cancel", callback_data=f"numeric_kb$cancel_{keyboard_id}")
    clear_btn = InlineKeyboardButton("↻ Clear", callback_data=f"numeric_kb$clear_{keyboard_id}")
    delete_btn = InlineKeyboardButton("⌫ Delete", callback_data=f"numeric_kb$delete_{keyboard_id}")
    back_btn = InlineKeyboardButton(BACK_BUTTON, callback_data=f"back_to_start")

    # Arrange buttons into rows
    markup.row(cancel_btn, clear_btn, delete_btn)
    markup.row(one_btn, two_btn, three_btn)
    markup.row(four_btn, five_btn, six_btn)
    markup.row(seven_btn, eight_btn, nine_btn)
    markup.row(dot_btn, zero_btn, enter_btn)
    markup.row(percent_10_btn, percent_25_btn, percent_50_btn, percent_100_btn)
    markup.row(back_btn)

    # Return the markup and message
    return markup


async def create_inline_numeric_keyboard(callback_query: types.CallbackQuery, context_id, edit, state: FSMContext):
    keyboard_id = generate_id()

    string_builder, activation_function, cancellation_function, max_number, min_number, message_response_type = await context_id_to_params(
        context_id, callback_query.from_user.id)

    if not max_number or not min_number:
        await callback_query.answer(string_builder, show_alert=True)
        return False

    user_id = str(callback_query.from_user.id)
    current_number = ""
    markup = await inline_numeric_keyboard(keyboard_id)
    msg = await string_builder(current_number)
    await local_storage.post_resource(keyboard_id,
                                      {"user_id": user_id, "current_number": current_number,
                                       "max_number": max_number, "min_number": min_number,
                                       "string_builder": function_to_bytes(string_builder),
                                       "activation_function": function_to_bytes(activation_function),
                                       "cancellation_function": function_to_bytes(cancellation_function),
                                       "message_response_type": function_to_bytes(message_response_type)})

    if edit:
        await callback_query.message.edit_text(text=msg, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
    else:
        await callback_query.message.answer(text=msg, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)


async def put_inline_numeric_keyboard(callback_query: types.CallbackQuery):
    params = extract_callback_data(callback_query.data)
    type_ = params[0]
    keyboard_id = params[-1]
    keyboard_data = await local_storage.get_resource(keyboard_id)
    if keyboard_data is None:
        return False
    user_id = keyboard_data['user_id']
    current_number = keyboard_data['current_number']
    max_number = keyboard_data['max_number']
    min_number = keyboard_data['min_number']
    string_builder = bytes_to_function(keyboard_data['string_builder'])
    cancellation_function = bytes_to_function(keyboard_data['cancellation_function'])
    activation_function = bytes_to_function(keyboard_data['activation_function'])
    message_response_type = bytes_to_function(keyboard_data['message_response_type'])

    if user_id != str(callback_query.from_user.id):
        await callback_query.answer("Action failed! You do not have creator permissions for this keyboard.")
        return False

    elif type_ == 'num':
        await handle_num_inline_numeric_keyboard(params, current_number, callback_query, max_number, min_number,
                                                 string_builder, keyboard_id)

    elif type_ == 'percent':
        await handle_percent_inline_numeric_keyboard(params, current_number, callback_query, max_number,
                                                     string_builder, keyboard_id)

    elif type_ == 'delete':
        await handle_delete_inline_numeric_keyboard(current_number, callback_query,
                                                    string_builder, keyboard_id)

    elif type_ == 'clear':
        await handle_clear_inline_numeric_keyboard(current_number, callback_query,
                                                   string_builder, keyboard_id)

    elif type_ == 'enter':
        await handle_enter_inline_numeric_keyboard(callback_query, current_number, activation_function, keyboard_id,
                                                   message_response_type, min_number, max_number)

    elif type_ == 'cancel':
        await handle_cancel_inline_numeric_keyboard(callback_query, cancellation_function, keyboard_id,
                                                    message_response_type)


async def handle_num_inline_numeric_keyboard(params, current_number, callback_query, max_number, min_number,
                                             string_builder, keyboard_id):
    num = params[1]
    new_number = str(current_number) + num

    if current_number == new_number:
        return False

    if not is_float(new_number):
        await callback_query.answer("Invalid entry. Please enter a valid number.")
        return False

    if float(new_number) > max_number:
        await callback_query.answer(f"Invalid entry. Please enter number from {min_number} to {max_number}.")
        return False

    if len(new_number) > CURRENCY_MAXIMUM_DIGITS:
        await callback_query.answer(f"Invalid entry. Too many digits")
        return False

    msg = await string_builder(new_number)
    await local_storage.put_resource(keyboard_id, {"current_number": new_number})

    markup = await inline_numeric_keyboard(keyboard_id)
    await callback_query.message.edit_text(text=msg, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)


async def handle_percent_inline_numeric_keyboard(params, current_number, callback_query, max_number,
                                                 string_builder, keyboard_id):
    percent = params[1]
    new_number = str(round(max_number * (float(percent) / 100), CURRENCY_MAXIMUM_DIGITS))
    if current_number == new_number:
        return False
    msg = await string_builder(new_number)
    await local_storage.put_resource(keyboard_id, {"current_number": new_number})

    markup = await inline_numeric_keyboard(keyboard_id)
    await callback_query.message.edit_text(text=msg, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)


async def handle_delete_inline_numeric_keyboard(current_number, callback_query,
                                                string_builder, keyboard_id):
    new_number = current_number[:-1]
    if current_number == new_number:
        return False
    if len(new_number) < 0:
        await callback_query.answer(f"Invalid entry.")
        return False

    msg = await string_builder(new_number)
    await local_storage.put_resource(keyboard_id, {"current_number": new_number})

    markup = await inline_numeric_keyboard(keyboard_id)
    await callback_query.message.edit_text(text=msg, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)


async def handle_clear_inline_numeric_keyboard(current_number, callback_query,
                                               string_builder, keyboard_id):
    new_number = ''
    if current_number == new_number:
        return False
    msg = await string_builder(new_number)
    await local_storage.put_resource(keyboard_id, {"current_number": new_number})

    markup = await inline_numeric_keyboard(keyboard_id)
    await callback_query.message.edit_text(text=msg, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)


async def handle_enter_inline_numeric_keyboard(callback_query, current_number, activation_function, keyboard_id,
                                               message_response_type: MessageResponseType, min_number, max_number):
    if not is_float(current_number):
        await callback_query.answer("Invalid entry. Please enter a valid number.")
        return False
    if float(current_number) < min_number:
        await callback_query.answer(f"Invalid entry. Please enter number from {min_number} to {max_number}.")
        return False
    await activation_function(callback_query, float(current_number), message_response_type)
    await local_storage.delete_resource(keyboard_id)


async def handle_cancel_inline_numeric_keyboard(callback_query, cancellation_function, keyboard_id,
                                                message_response_type: MessageResponseType):
    await cancellation_function(callback_query, message_response_type)
    await local_storage.delete_resource(keyboard_id)
