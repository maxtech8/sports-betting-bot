from aiogram import types
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton

import TermsAndConditions
import User
from APIs.APIsSingleton import APIsSingleton
from Configurations.BotConfig import BOT_USERNAME
from Configurations.Enablers import REQUIRE_TERMS_AND_CONDITIONS
from Wallet.Functions import get_user_wallets

APIs_singleton = APIsSingleton.get_instance()
champions_api = APIs_singleton.get_champions_api()


async def get_welcome_keyboards(user_id, first_name):
    msg = f"👋 Hello *{first_name}*, welcome to the best crypto sport bets Telegram bot!"

    markup = InlineKeyboardMarkup()
    sportsbook_btn = InlineKeyboardButton("⚽ Sportsbook",
                                          callback_data=f"create_pager$50_0")
    flash_btn = InlineKeyboardButton("⚡ Instant Bet", callback_data="create_pager$150_0")

    wallet_btn = InlineKeyboardButton("👛 Wallet", callback_data="view_wallet")
    about_btn = InlineKeyboardButton("💡 About", callback_data="about$0")
    my_bets_btn = InlineKeyboardButton("📋 My Bets", callback_data=f"create_pager$65_{user_id}")
    pool_btn = InlineKeyboardButton("🏦 Pool", callback_data=f"open_pool")

    # search_btn = InlineKeyboardButton(text="🔍 Search", switch_inline_query_current_chat="")

    markup.row(sportsbook_btn, flash_btn)
    markup.row(about_btn, wallet_btn)
    markup.row(my_bets_btn, pool_btn)
    return markup, msg


async def show_balance(message: types.Message):
    user = await champions_api.get_user(message.from_user.id)

    if not user:

        result = await User.Functions.create_user(message.from_user.id)
        if not result:
            print("Error in creating new user user should try again later")
            return False
        else:
            user = await champions_api.get_user(message.from_user.id)

    wallets = await get_user_wallets(message.from_user.id)
    msg = f'💰 *{message.from_user.first_name}* Wallet\n\n'
    for wallet in wallets:
        msg += "• `" + str(wallet['balance']) + "`" + "  " + wallet['wallet_type'] + "\n"

    #   pprint(wallets)
    await message.answer(msg, disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN)


async def start_bot(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    message = await message.answer("⏳ Loading ..")
    user = await champions_api.get_user(user_id)

    if not user:

        result = await User.Functions.create_user(user_id)
        if not result:
            print("Error in creating new user user should try again later")
            return False
        else:
            user = await champions_api.get_user(user_id)

    if (user and user['user'][
        'terms_and_conditions_approved']) or not REQUIRE_TERMS_AND_CONDITIONS:  # No terms and conditions at the moment
        keyboard, msg = await get_welcome_keyboards(user_id, first_name)

    else:
        keyboard, msg = await TermsAndConditions.Functions.get_terms_and_conditions_agree_keyboard()

    await message.edit_text(msg, reply_markup=keyboard, disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN)


async def back_to_start(callback_query: types.CallbackQuery):
    keyboard, msg = await get_welcome_keyboards(callback_query.from_user.id, callback_query.from_user.first_name)
    await callback_query.message.edit_text(msg, reply_markup=keyboard, disable_web_page_preview=True,
                                           parse_mode=ParseMode.MARKDOWN)
