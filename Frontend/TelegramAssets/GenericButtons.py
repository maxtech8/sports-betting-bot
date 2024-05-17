from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Configurations.BotConfig import SUPPORT_USERNAME


async def get_close_button():
    return InlineKeyboardButton("Close", callback_data=f"close")
async def get_help_button():
    return InlineKeyboardButton("💁 Help", url=f"https://t.me/{SUPPORT_USERNAME}")
