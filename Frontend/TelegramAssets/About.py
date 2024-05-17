from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Configurations.BotConfig import BOT_USERNAME, SUPPORT_USERNAME
from Configurations.StringConstants import NEXT_BUTTON, PREVIOUS_BUTTON, BACK_BUTTON
from TelegramAssets.GenericButtons import get_help_button

PAGE_1 = f"""
📖 *Welcome to Bets Bot* 🎉

Dive into the ultimate sports betting experience on Telegram! 
🏆 Safely deposit cryptocurrencies like ETH and BNB, 
and place bets on your favorite sports events. 
Whether it's the dynamic ⚽ soccer matches or thrilling 🏀 basketball games,
 we've got all your sporting passions covered!
"""

PAGE_2 = """
📖 *Getting Started*

Embark on your betting journey with peace of mind.
This platform is designed exclusively for adults 🔞,
promoting responsible gambling. Remember,
bet within your means and set sensible limits.
Your well-being is our top priority! 💵
"""

PAGE_3 = """
📖 *Security & Privacy*

Your trust is our cornerstone.
Rest assured, your privacy is sacred to us.
We uphold the highest standards of security,
ensuring your personal information remains confidential and protected, always. 🔒
"""

PAGE_4 = f"""
📖 *Support & Assistance*

Encounter a hurdle? Our dedicated support team stands ready 24/7 to guide you through.
For swift assistance, tap the 'Help' button or reach out to us directly at @{SUPPORT_USERNAME}.
Your seamless betting experience is our commitment. 💬
"""

PAGE_5 = """
📖 *Embark on Your Betting Adventure*

The stage is set, the odds are in your favor, and a world of betting awaits.
Deposit your crypto and discover a plethora of betting opportunities. Stay on the lookout for exclusive promotions,
enticing bonuses, and insider tips. Your next big win is just a bet away! 🚀🌟
"""

PAGES = [PAGE_1, PAGE_2, PAGE_3, PAGE_4, PAGE_5]


async def create_about_keyboard(current_page):
    current_page = int(current_page)
    msg = PAGES[current_page]

    markup = InlineKeyboardMarkup()
    next_btn = InlineKeyboardButton(NEXT_BUTTON, callback_data=f"about${(current_page + 1) % len(PAGES)}")
    page_btn = InlineKeyboardButton(f"{current_page + 1}/{len(PAGES)}", callback_data=f"NOOP")
    prev_btn = InlineKeyboardButton(PREVIOUS_BUTTON,
                                    callback_data=f"about${(current_page - 1 + len(PAGES)) % len(PAGES)}")
    back_btn = InlineKeyboardButton(BACK_BUTTON, callback_data=f"back_to_start")

    markup.row(prev_btn, page_btn, next_btn)
    markup.row(await get_help_button())
    markup.row(back_btn)

    return markup, msg


async def open_about(callback_query: types.CallbackQuery, page):
    markup, msg = await create_about_keyboard(page)
    await callback_query.message.edit_text(text=msg, reply_markup=markup, parse_mode=types.ParseMode.MARKDOWN)
