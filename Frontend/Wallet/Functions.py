from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from APIs.APIsSingleton import APIsSingleton
from Configurations.StringConstants import BACK_BUTTON, get_select_address_message, HOME_BUTTON
from Database.LocalStorage import LocalStorage
from TelegramAssets.GenericButtons import get_close_button
from TelegramAssets.MessageResponseType import MessageResponseType
from User.Functions import get_user
from Utils.Generators import generate_wallet_address_qr_code, generate_id

local_storage = LocalStorage.get_instance()

APIs_singleton = APIsSingleton.get_instance()
champions_api = APIs_singleton.get_champions_api()


async def confirm_withdrawal(callback_query: types.CallbackQuery, confirmation_id):
    try:
        # Retrieve confirmation data from local storage
        confirmation_data = await local_storage.get_resource(confirmation_id)
        user_id = confirmation_data['user_id']
        wallet_type = confirmation_data['wallet_type']
        amount = confirmation_data['amount']
        network = confirmation_data['network']
        address = confirmation_data['address']

        # Send withdrawal request to the backend/API
        response = await champions_api.withdrawal_external_address(confirmation_data, confirmation_id)
        print(f"Response from withdrawal API: {response}")

        # Check if the transaction hash is present in the response
        if 'tx_hash' in response['response']:
            tx_hash = response['response']['tx_hash']
            explorer_link = await (await WithdrawKeyboardFactory.get_class(wallet_type)).get_explorer_link(tx_hash)
            msg = (f"✅ Withdrawal request submitted successfully!\n\n"
                   f"• *Withdrawal ID:* `{confirmation_id}`\n"
                   f"• *Transaction Hash:* `{tx_hash}`\n\n"
                   f"You can track the transaction on the [{network} blockchain explorer]({explorer_link}).\n\n"
                   )

        else:
            msg = f"⚠️ Withdrawal request could not be processed. Please try again or contact support for assistance.\n\nWithdrawal ID: `{confirmation_id}`"

        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton(text=HOME_BUTTON, callback_data="back_to_start"))
        # Send the message to the user
        await callback_query.message.edit_text(msg, reply_markup=markup, parse_mode=types.ParseMode.MARKDOWN,
                                               disable_web_page_preview=True)

    except Exception as e:
        # Log the exception and notify the user of a system error
        print(f"An error occurred during the withdrawal confirmation: {e}")
        await callback_query.message.answer(
            "❗️ An unexpected error occurred while processing your request. Please try again later or contact support.\n\nWithdrawal ID: `{confirmation_id}`")


async def create_withdraw_confirm_keyboard(wallet_type, amount, network, address, confirmation_id):
    markup = InlineKeyboardMarkup()

    confirmation_message = (
        f"🔍 Please review the details carefully. Ensure that the address and amount are correct.\n\n"
        f"• Amount: *{amount} {wallet_type}* \n"
        f"• Network: *{network}*\n"
        f"• Receiving address: `{address}`\n\n"
        f"⚠️ _Once confirmed, the transaction cannot be reversed._"
    )
    back_btn = InlineKeyboardButton(BACK_BUTTON, callback_data="back_to_start")
    confirm_btn = InlineKeyboardButton("✅ Confirm",
                                       callback_data=f"confirm_withdrawal${confirmation_id}")

    markup.row(back_btn, confirm_btn)

    return markup, confirmation_message


async def insert_external_address(message, bot):
    message_id = message.message_id
    reply_to_message_id = message.reply_to_message.message_id
    chat_id = message.chat.id
    reply_to_chat_id = message.reply_to_message.chat.id
    user_id = str(message.from_user.id)
    result = await local_storage.put_resource(
        "insert_external_address_" + user_id, {"address": message.text})

    await bot.delete_message(chat_id=chat_id, message_id=message_id)
    await bot.delete_message(chat_id=reply_to_chat_id, message_id=reply_to_message_id)
    if not result:
        return False

    insert_external_address_data = await local_storage.get_resource(
        "insert_external_address_" + user_id)

    message_id = insert_external_address_data['message_id']
    confirmation_id = generate_id()
    wallet_type = insert_external_address_data['wallet_type']
    amount = insert_external_address_data['amount']
    network = insert_external_address_data['network']
    address = insert_external_address_data['address']
    keyboard, msg = await create_withdraw_confirm_keyboard(wallet_type, amount, network, address, confirmation_id)
    await local_storage.post_resource(confirmation_id,
                                      {"user_id": user_id, "wallet_type": wallet_type, "amount": amount,
                                       "network": network,
                                       "address": address})
    await bot.edit_message_text(text=msg, reply_markup=keyboard, chat_id=chat_id, message_id=message_id,
                                parse_mode=types.ParseMode.MARKDOWN)

    # await local_storage.delete_resource("insert_external_address_" + str(message.from_user.id))


async def set_withdrawal(callback_query: types.CallbackQuery,
                         method, wallet_type, state: FSMContext):
    # External Address
    if method == "ea":
        txt = get_select_address_message(wallet_type)
        await callback_query.message.answer(text=txt,
                                            reply_markup=types.ForceReply(selective=True))


async def create_deposit_keyboard(wallet):
    wallet_type = wallet['wallet_type']
    markup = InlineKeyboardMarkup()
    wlt_cls = await WithdrawKeyboardFactory.get_class(wallet_type)
    msg = f"""    
📥 Use the address below to deposit coins.

Coin: *{wallet_type}*
Network: *{wlt_cls.network}*

`{wallet['deposit_key']}`

Min deposit: *{await wlt_cls.get_minimum_deposit()}* {wallet_type}

⚠️ _Send only {wallet_type} via {wlt_cls.network} to this address, otherwise coins will be lost. You must send at least {await wlt_cls.get_minimum_deposit()} {wallet_type} or more to deposit._

"""
    qr_code_generator = InlineKeyboardButton("◼ QR Code",
                                             callback_data=f"generate_qr_code")
    back_btn =  InlineKeyboardButton(BACK_BUTTON,
                                             callback_data=f"back_to_start")
    markup.row(qr_code_generator)
    markup.row(back_btn)

    return markup, msg


async def create_switch_wallet_keyboard(wallets, active_wallet_type):
    markup = InlineKeyboardMarkup()

    msg = f'👛 Select Wallet:'

    for wallet in wallets:
        if wallet['wallet_type'] == active_wallet_type:
            wallet_type = InlineKeyboardButton("• " + wallet['wallet_type'] + " •",
                                               callback_data=f"select_active_wallet_type${wallet['wallet_type']}")
        else:
            wallet_type = InlineKeyboardButton(wallet['wallet_type'],
                                               callback_data=f"select_active_wallet_type${wallet['wallet_type']}")
        markup.row(wallet_type)

    return markup, msg


async def create_keyboard(wallet, active_wallet_type, user_id):
    markup = InlineKeyboardMarkup()

    msg = f'👛 *{wallet["wallet_type"]} Wallet*\n\nBalance: `{wallet["balance"]}` {wallet["wallet_type"]}'

    # Define buttons
    deposit = InlineKeyboardButton("📥 Deposit", callback_data=f"deposit")
    withdraw = InlineKeyboardButton("📤 Withdraw",
                                    callback_data=f"create_inline_num_kb${MessageResponseType.EDIT}_WLT#{active_wallet_type}")
    switch_wallet = InlineKeyboardButton("💱 Switch Wallet", callback_data=f"switch_wallet")
    back_btn = InlineKeyboardButton(BACK_BUTTON, callback_data=f"back_to_start")

    # Arrange buttons into rows
    markup.row(deposit, withdraw)
    markup.row(switch_wallet)
    markup.row(back_btn)

    # Return the markup and message
    return markup, msg


async def switch_wallet(callback_query: types.CallbackQuery, state: FSMContext):
    user_wallets = await get_user_wallets(callback_query.from_user.id)
    users_data = await state.get_data()
    if 'active_wallet_type' not in users_data:
        await state.set_data({"active_wallet_type": "DEMO_CRYPTO"})
    users_data = await state.get_data()
    active_wallet_type = users_data['active_wallet_type']
    markup, msg = await create_switch_wallet_keyboard(user_wallets, active_wallet_type)
    await callback_query.message.edit_text(text=msg, reply_markup=markup)


async def view_wallet(callback_query: types.CallbackQuery, state: FSMContext):
    user_wallets = await get_user_wallets(callback_query.from_user.id)
    users_data = await state.get_data()
    if 'active_wallet_type' not in users_data:
        await state.set_data({"active_wallet_type": "DEMO"})
    users_data = await state.get_data()
    active_wallet_type = users_data['active_wallet_type']
    for wallet in user_wallets:
        if wallet['wallet_type'] == active_wallet_type:
            markup, msg = await create_keyboard(wallet, active_wallet_type, callback_query.from_user.id)
            await callback_query.message.edit_text(text=msg, reply_markup=markup, parse_mode=types.ParseMode.MARKDOWN)


async def get_user_wallets(user_id: str):
    user_data = await get_user(user_id)
    return user_data['user']['wallets'] if user_data else None


async def select_active_wallet_type(callback_query: types.CallbackQuery, active_wallet_type, state: FSMContext):
    await state.update_data({"active_wallet_type": active_wallet_type})
    await view_wallet(callback_query, state)


async def deposit(callback_query: types.CallbackQuery, state: FSMContext):
    user_wallets = await get_user_wallets(callback_query.from_user.id)
    users_data = await state.get_data()
    if 'active_wallet_type' not in users_data:
        await callback_query.message.edit_text("Failed, please try again!")
        return False

    for wallet in user_wallets:
        if wallet['wallet_type'] == users_data['active_wallet_type']:
            if wallet['wallet_type'] == 'DEMO':
                await callback_query.answer(f"You can not deposit DEMO at the moment!", show_alert=True)

            else:
                markup, msg = await create_deposit_keyboard(wallet)
                await callback_query.message.edit_text(text=msg, reply_markup=markup, parse_mode=types.ParseMode.MARKDOWN)


async def generate_qr_code(callback_query: types.CallbackQuery, state: FSMContext):
    user_wallets = await get_user_wallets(callback_query.from_user.id)
    users_data = await state.get_data()
    button = await get_close_button()
    markup = InlineKeyboardMarkup()
    markup.row(button)

    if 'active_wallet_type' not in users_data:
        await callback_query.message.edit_text("Failed, please try again!")
        return False

    for wallet in user_wallets:
        if wallet['wallet_type'] == users_data['active_wallet_type']:
            wallet_address = wallet['deposit_key']
            await callback_query.message.answer_photo(generate_wallet_address_qr_code(wallet_address),
                                                      reply_markup=markup)


class WithdrawKeyboardFactory:

    @staticmethod
    async def get_class(wallet_type):
        if wallet_type == 'DEMO':
            return DEMO
        if wallet_type == "BNB":
            return BNB
        if wallet_type == "ETH":
            return ETH
        if wallet_type == "SOL":
            return SOL


class DEMO:

    @staticmethod
    async def create_keyboard():
        markup = InlineKeyboardMarkup()

        set_address = InlineKeyboardButton("Set Address",
                                           callback_data=f"set_withdraw$sa")
        crypto_bot = InlineKeyboardButton("Crypto Bot",
                                          callback_data=f"set_withdraw$cb")

        # Arrange buttons into rows
        markup.row(set_address, crypto_bot)
        return markup

    @staticmethod
    async def get_minimum_withdraw():
        return 0.00001

    @staticmethod
    async def get_minimum_deposit():
        return 0.00001

    @staticmethod
    async def withdraw_keyboard_string(number):
        return "Enter *CRYPTO* amount: `" + str(number) + "`"

    @staticmethod
    async def withdraw_keyboard_cancel(callback_query: types.CallbackQuery, type_: MessageResponseType):
        edit = type_ == MessageResponseType.EDIT
        if edit:
            await callback_query.message.edit_text(f"Cancel")
        else:
            await callback_query.message.answer(text=f"Cancel")

    @staticmethod
    async def withdraw_keyboard_enter(callback_query: types.CallbackQuery, value: float, type_: MessageResponseType):
        withdraw_request_id = generate_id()
        await local_storage.post_resource(withdraw_request_id,
                                          {"wallet_type": "DEMO", "amount": value, "network": None, "address": None})
        edit = type_ == MessageResponseType.EDIT

        if edit:
            await callback_query.message.edit_text(
                f"Withdraw:\n\n{value} DEMO \n\n Your current address: empty",
                reply_markup=await DEMO.create_keyboard())
        else:
            await callback_query.message.answer(
                f"Withdraw:\n\n{value} DEMO \n\n Your current address: empty",
                reply_markup=await DEMO.create_keyboard())

    @staticmethod
    async def get_balance(user_id):
        user_wallets = await get_user_wallets(user_id)
        for wallet in user_wallets:
            if wallet['wallet_type'] == 'DEMO':
                return wallet['balance']


class BNB:
    network = "Binance Smart Chain (BEP20)"

    @staticmethod
    async def get_explorer_link(tx_hash):
        return f"https://bscscan.com/tx/{tx_hash}"

    @staticmethod
    async def create_keyboard():
        markup = InlineKeyboardMarkup()

        set_address = InlineKeyboardButton("External Address",
                                           callback_data=f"set_withdrawal$ea_BNB")
        # crypto_bot = InlineKeyboardButton("Crypto Bot",
        #                                   callback_data=f"set_withdraw$cb")

        # Arrange buttons into rows
        markup.row(set_address)
        return markup

    @staticmethod
    async def get_minimum_withdraw():
        return 0.002

    @staticmethod
    async def get_minimum_deposit():
        return 0.002

    @staticmethod
    async def withdraw_keyboard_string(number):
        return "Enter *BNB* amount: `" + str(number) + "`"

    @staticmethod
    async def withdraw_keyboard_cancel(callback_query: types.CallbackQuery, type_: MessageResponseType):
        edit = type_ == MessageResponseType.EDIT
        if edit:
            await callback_query.message.edit_text(f"Cancel")
        else:
            await callback_query.message.answer(text=f"Cancel")

    @staticmethod
    async def withdraw_keyboard_enter(callback_query: types.CallbackQuery, value: float, type_: MessageResponseType):
        await local_storage.post_resource("insert_external_address_" + str(callback_query.from_user.id),
                                          {"wallet_type": "BNB", "amount": value,
                                           "network": BNB.network, "message_id": callback_query.message.message_id})

        edit = type_ == MessageResponseType.EDIT
        if edit:
            await callback_query.message.edit_text(
                f"📤 Choose how to send `{value}` BNB",
                reply_markup=await BNB.create_keyboard(), parse_mode=types.ParseMode.MARKDOWN)
        else:
            await callback_query.message.answer(
                f"📤 Choose how to send `{value}` BNB",
                reply_markup=await BNB.create_keyboard(), parse_mode=types.ParseMode.MARKDOWN)

    @staticmethod
    async def get_balance(user_id):
        user_wallets = await get_user_wallets(user_id)
        for wallet in user_wallets:
            if wallet['wallet_type'] == 'BNB':
                return wallet['balance']


class ETH:
    network = "Ethereum (ERC20)"

    @staticmethod
    async def get_explorer_link(tx_hash):
        return f"https://etherscan.io/tx/{tx_hash}"

    @staticmethod
    async def create_keyboard():
        markup = InlineKeyboardMarkup()

        set_address = InlineKeyboardButton("External Address",
                                           callback_data=f"set_withdrawal$ea_ETH")
        # crypto_bot = InlineKeyboardButton("Crypto Bot",
        #                                   callback_data=f"set_withdraw$cb")

        # Arrange buttons into rows
        markup.row(set_address)
        return markup

    @staticmethod
    async def get_minimum_withdraw():
        return 0.002

    @staticmethod
    async def get_minimum_deposit():
        return 0.002

    @staticmethod
    async def withdraw_keyboard_string(number):
        return "Enter *ETH* amount: `" + str(number) + "`"

    @staticmethod
    async def withdraw_keyboard_cancel(callback_query: types.CallbackQuery, type_: MessageResponseType):
        edit = type_ == MessageResponseType.EDIT
        if edit:
            await callback_query.message.edit_text(f"Cancel")
        else:
            await callback_query.message.answer(text=f"Cancel")

    @staticmethod
    async def withdraw_keyboard_enter(callback_query: types.CallbackQuery, value: float, type_: MessageResponseType):
        await local_storage.post_resource("insert_external_address_" + str(callback_query.from_user.id),
                                          {"wallet_type": "ETH", "amount": value,
                                           "network": ETH.network, "message_id": callback_query.message.message_id})
        edit = type_ == MessageResponseType.EDIT

        if edit:
            await callback_query.message.edit_text(
                f"📤 Choose how to send `{value}` ETH",
                reply_markup=await ETH.create_keyboard(), parse_mode=types.ParseMode.MARKDOWN)
        else:
            await callback_query.message.answer(
                f"📤 Choose how to send `{value}` ETH",
                reply_markup=await ETH.create_keyboard(), parse_mode=types.ParseMode.MARKDOWN)

    @staticmethod
    async def get_balance(user_id):
        user_wallets = await get_user_wallets(user_id)
        for wallet in user_wallets:
            if wallet['wallet_type'] == 'ETH':
                return wallet['balance']

class SOL:
    network = "Solana"

    @staticmethod
    async def get_explorer_link(tx_hash):
        return f"https://solscan.io/tx/{tx_hash}"

    @staticmethod
    async def create_keyboard():
        markup = InlineKeyboardMarkup()

        set_address = InlineKeyboardButton("External Address",
                                           callback_data=f"set_withdrawal$ea_SOL")
        # crypto_bot = InlineKeyboardButton("Crypto Bot",
        #                                   callback_data=f"set_withdraw$cb")

        # Arrange buttons into rows
        markup.row(set_address)
        return markup

    @staticmethod
    async def get_minimum_withdraw():
        return 0.1

    @staticmethod
    async def get_minimum_deposit():
        return 0.1

    @staticmethod
    async def withdraw_keyboard_string(number):
        return "Enter *SOL* amount: `" + str(number) + "`"

    @staticmethod
    async def withdraw_keyboard_cancel(callback_query: types.CallbackQuery, type_: MessageResponseType):
        edit = type_ == MessageResponseType.EDIT
        if edit:
            await callback_query.message.edit_text(f"Cancel")
        else:
            await callback_query.message.answer(text=f"Cancel")

    @staticmethod
    async def withdraw_keyboard_enter(callback_query: types.CallbackQuery, value: float, type_: MessageResponseType):
        await local_storage.post_resource("insert_external_address_" + str(callback_query.from_user.id),
                                          {"wallet_type": "SOL", "amount": value,
                                           "network": SOL.network, "message_id": callback_query.message.message_id})
        edit = type_ == MessageResponseType.EDIT

        if edit:
            await callback_query.message.edit_text(
                f"📤 Choose how to send `{value}` SOL",
                reply_markup=await SOL.create_keyboard(), parse_mode=types.ParseMode.MARKDOWN)
        else:
            await callback_query.message.answer(
                f"📤 Choose how to send `{value}` SOL",
                reply_markup=await SOL.create_keyboard(), parse_mode=types.ParseMode.MARKDOWN)

    @staticmethod
    async def get_balance(user_id):
        user_wallets = await get_user_wallets(user_id)
        for wallet in user_wallets:
            if wallet['wallet_type'] == 'SOL':
                return wallet['balance']