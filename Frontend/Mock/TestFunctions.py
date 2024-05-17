from aiogram import types

from TelegramAssets.MessageResponseType import MessageResponseType


async def mock_keyboard_enter(callback_query: types.CallbackQuery, value: float, type_: MessageResponseType):
    edit = type_ == MessageResponseType.EDIT
    if edit:
        await callback_query.message.edit_text(f"Entered number {value}")
    else:
        await callback_query.message.answer(text=f"Entered number {value}")


async def mock_keyboard_cancel(callback_query: types.CallbackQuery, type_: MessageResponseType):
    edit = type_ == MessageResponseType.EDIT
    if edit:
        await callback_query.message.edit_text(f"Cancel")
    else:
        await callback_query.message.answer(text=f"Cancel")


async def mock_keyboard_string(x):
    return "Enter *USDT* amount: `" + str(
        x) + "`"
