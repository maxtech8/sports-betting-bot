from pprint import pprint

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from APIs.APIsSingleton import APIsSingleton
from Configurations.StringConstants import BACK_BUTTON
from TelegramAssets.GenericButtons import get_close_button

APIs_singleton = APIsSingleton.get_instance()
champions_api = APIs_singleton.get_champions_api()


async def open_pool(message: types.Message):
    data = await champions_api.get_pool()
    pool = data['response']
    queue = pool['queue']
    wallets = pool['wallets']
    msg = '🏦 *Liquidity Pool*\n\n'
    for wallet_name, wallet_data in wallets.items():
        debt = 0
        queue_len = 0
        for member in queue:
            if member['wallet_type'] == wallet_name:
                queue_len += 1
                debt += member['amount']
        msg += f'• *{wallet_name}* Balance: `{wallet_data["balance"] - debt}` ' +( f'_({queue_len} players in queue)_\n\n' if queue_len > 0 else '\n\n')
    close_btn = await get_close_button()
    markup = InlineKeyboardMarkup()
    markup.row(close_btn)
    await message.answer(text=msg, reply_markup=markup, parse_mode=types.ParseMode.MARKDOWN)

async def open_pool_cbq(call_backquery: types.CallbackQuery):
    data = await champions_api.get_pool()
    pprint(data)
    pool = data['response']
    queue = pool['queue']
    wallets = pool['wallets']
    msg = '🏦 *Liquidity Pool*\n\n'
    for wallet_name, wallet_data in wallets.items():
        debt = 0
        queue_len = 0
        for member in queue:
            if member['wallet_type'] == wallet_name:
                queue_len += 1
                debt += member['amount']
        msg += f'• *{wallet_name}* Balance: `{wallet_data["balance"] - debt}` ' +( f'_({queue_len} players in queue)_\n\n' if queue_len > 0 else '\n\n')
    close_btn = InlineKeyboardButton(BACK_BUTTON, callback_data=f"back_to_start")
    markup = InlineKeyboardMarkup()
    markup.row(close_btn)
    await call_backquery.message.edit_text(text=msg, reply_markup=markup, parse_mode=types.ParseMode.MARKDOWN)
