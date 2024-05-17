import requests
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

import Start.Functions
from TermsAndConditions.Constants import TERMS_AND_CONDITIONS_AGREE

BASE_URL = "http://127.0.0.1:5000/api/v1"


async def get_terms_and_conditions_agree_keyboard():
    # Main menu keyboard
    terms_and_cond_url = "https://telegra.ph/Terms-and-Conditions-for-Champions-Sports-Betting-Bot-12-26"
    msg = f"Before proceeding, please review and agree to our "
    msg += f'<a href="{terms_and_cond_url}">Terms and Conditions</a>.'
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, selective=True,
                                   input_field_placeholder="I agree to all of the terms and conditions")
    keyboard.row(KeyboardButton(TERMS_AND_CONDITIONS_AGREE))
    return keyboard, msg


async def request_to_approve_terms_and_conditions(user_id):
    """POST request to approve terms and conditions for a user."""
    data = {'user_id': user_id}
    response = requests.post(f"{BASE_URL}/approveTermsAndConditions", json=data)
    if response.status_code == 200:  # Assuming 200 is the success code for approval
        return True
    else:
        print("Failed to approve terms and conditions", response.status_code)
        return False


async def approve_terms_and_conditions(message: types.Message):
    await request_to_approve_terms_and_conditions(message.from_user.id)
    await Start.Functions.start_bot(message)
