from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

from APIs.APIsSingleton import APIsSingleton
from Configurations.StringConstants import BACK_BUTTON
from Database.LocalStorage import LocalStorage
from TelegramAssets.MessageResponseType import MessageResponseType
from Utils.Generators import generate_id
from Utils.StringShortener import StringShortener
from Utils.Validators import is_float

local_storage = LocalStorage.get_instance()
APIs_singleton = APIsSingleton.get_instance()
champions_api = APIs_singleton.get_champions_api()

ss = StringShortener()

class AmountSelector:
    def __init__(self, event_id, sport_id, selected_market_key_name, odd_id, wallet_type):
        self.event_id = event_id
        self.sport_id = sport_id
        self.selected_market_key_name = selected_market_key_name
        self.odd_id = odd_id
        self.wallet_type = wallet_type
        self.bet_request_id = generate_id()

    async def create_keyboard(self):
        markup = InlineKeyboardMarkup()
        callback_data = f"sel_odd${ss.shorten(self.event_id)}_{self.sport_id}_{ss.shorten(self.selected_market_key_name)}_{self.odd_id}_default"

        modify_amount = InlineKeyboardButton("🔢 Modify Price",
                                         callback_data=callback_data)
        place_bet = InlineKeyboardButton("✅ Register to Bet!",
                                         callback_data=f"place_bet${self.bet_request_id}")
        back_btn = InlineKeyboardButton(BACK_BUTTON, callback_data=f"back_to_start")

        # Arrange buttons into rows
        markup.row(place_bet)
        markup.row(back_btn, modify_amount)

        return markup

    async def get_minimum_withdraw(self):
        return 0.00001

    async def bet_amount_keyboard_string(self, number):
        odd = await champions_api.get_odd(self.event_id, self.sport_id, self.selected_market_key_name, self.odd_id)
        rate = odd["odd"]['rate']
        return f"Enter *{self.wallet_type}* price: `" + str(
            number) + "`" + f"\n\n🤑 *Est. Payout:* `{float(number) * rate if is_float(number) else number}`"

    async def withdraw_keyboard_cancel(self, callback_query: types.CallbackQuery, type_: MessageResponseType):
        edit = type_ == MessageResponseType.EDIT
        if edit:
            await callback_query.message.edit_text(f"Cancel")
        else:
            await callback_query.message.answer(text=f"Cancel")

    async def verify_bet(self, callback_query: types.CallbackQuery, value: float,
                         type_: MessageResponseType):
        odd = await champions_api.get_odd(self.event_id, self.sport_id, self.selected_market_key_name, self.odd_id)
        rate = odd["odd"]['rate']
        await local_storage.post_resource(self.bet_request_id,
                                          {"event_id": self.event_id, "amount": value, "sport_id": self.sport_id,
                                           "market_key_name": self.selected_market_key_name, "odd_id": self.odd_id,
                                           "wallet_type": self.wallet_type})
        edit = type_ == MessageResponseType.EDIT
        msg = f"""
🔍 *Bet Summary*
        
• *Price:* `{value}` {self.wallet_type}
• *Est. Payout: * `{rate * value}` {self.wallet_type}
• *Market:* {self.selected_market_key_name}
• *Side:* {self.odd_id}
• *Event ID:* `{self.event_id}`

⚠️ _By placing this bet, I acknowledge and accept any odds changes that may occur._
_Please review and confirm your bet by selecting an option below._
"""

        if edit:
            await callback_query.message.edit_text(
                msg,
                reply_markup=await self.create_keyboard(), parse_mode=ParseMode.MARKDOWN)
        else:
            await callback_query.message.answer(
                msg,
                reply_markup=await self.create_keyboard(), parse_mode=ParseMode.MARKDOWN)
