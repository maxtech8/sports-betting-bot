from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from Configurations.GamingConfig import FLASH_BET_PERCENTAGES
from Configurations.StringConstants import BACK_BUTTON
from Gaming.AmountSelector import AmountSelector
from TelegramAssets.MessageResponseType import MessageResponseType
from Wallet.Functions import WithdrawKeyboardFactory


async def create_flash_path(callback_query: types.CallbackQuery, event_id, sport_id, selected_market_key_name, odd_id,
                            currency):
    user_id = callback_query.from_user.id
    wlt = await WithdrawKeyboardFactory.get_class(currency)

    balance = await wlt.get_balance(user_id)
    minimum = await wlt.get_minimum_withdraw()
    bet_amount = balance * FLASH_BET_PERCENTAGES
    amount_selector = AmountSelector(event_id, sport_id, selected_market_key_name, odd_id, currency)

    if bet_amount < minimum:
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton(BACK_BUTTON,
                                        callback_data=f'back_to_start'))
        await callback_query.message.edit_text("Not enough balance, please deposit or switch wallet",reply_markup=markup)
    else:
        await amount_selector.verify_bet(callback_query, bet_amount, MessageResponseType.EDIT)
