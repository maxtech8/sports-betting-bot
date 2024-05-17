import asyncio
import time
from pprint import pprint

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

from APIs.APIsSingleton import APIsSingleton
from Configurations.StringConstants import get_sport_emoji, BACK_BUTTON, HOME_BUTTON
from Database.LocalStorage import LocalStorage
from Utils.Generators import generate_id, unix_time_to_gmt_string
from Utils.StringShortener import StringShortener

APIs_singleton = APIsSingleton.get_instance()
champions_api = APIs_singleton.get_champions_api()
local_storage = LocalStorage.get_instance()
ss = StringShortener()


async def build_title_from_teams(teams):
    try:
        title = ''
        for index, team in enumerate(teams):
            print(team)
            title += team['team_name']
            if index >= len(teams) - 1:
                return title
            title += " - "
        return False
    except TypeError:
        return False


async def get_my_bets_list(user_id):
    kb_list = []
    response = await champions_api.get_my_bets(user_id)

    history_bets = response['history_bets']
    live_bets = response['live_bets']
    print(live_bets)
    print(history_bets)
    for event_id, participant_data in live_bets.items():
        eid = generate_id()
        await local_storage.post_resource(eid, {"event_id": event_id, "participant": participant_data})
        kb_list.append({eid: "☑️ " + participant_data['odd']['odd_name']})

    for event_id, participant_data in history_bets.items():
        eid = generate_id()
        await local_storage.post_resource(eid, {"event_id": event_id, "participant": participant_data})
        kb_list.append({eid: "✅ " + participant_data['odd']['odd_name']})
    return kb_list


async def get_top_events_list():
    response = await get_sports()  # Assuming get_sports is defined elsewhere and returns the sports dictionary
    sports = response['sports']  # This is now expected to be a list of dictionaries
    kb_list = []
    if sports['code'] == 200:
        sport_data = sports['data']
    else:
        return False
    for sport_dict in sport_data:  # Iterating through each dictionary in the list
        for sport_id, details in sport_dict.items():  # Now getting sport_id and details
            sport_emoji = get_sport_emoji(details['SPORT_NAME'])
            leagues = await get_leagues(sport_id)
            for league in leagues['leagues']:
                response = await champions_api.get_events(sport_id, league['league_id'])
                if not response:
                    print("Failed to fetch get events from get_top_events_list")
                    continue

                for event in response['inplay_events']:
                    title = await build_title_from_teams(event['teams'])
                    if not title:
                        continue
                    else:
                        kb_list.append({sport_id + "+" + event['event_id'] + "+" + "flash": f"{sport_emoji} " + title})
                    break

        # kb_lst.append({sport_id: + " " + details['SPORT_NAME']})
    return kb_list


async def get_events_list(args):
    kb_list = []
    sport_id = args.split("+")[0]
    league_id = args.split("+")[1]
    response = await champions_api.get_events(sport_id, league_id)

    for event in response['inplay_events']:
        title = await build_title_from_teams(event['teams'])
        if not title:
            continue
        kb_list.append({sport_id + '+' + event['event_id']: "📺 " + title})
    for event in response['upcoming_events']:
        title = await build_title_from_teams(event['teams'])
        if not title:
            continue
        kb_list.append({sport_id + "+" + event['event_id'] + "+" + "default": "📅 " + title})
    return kb_list


async def get_leagues_list(sport_id):
    kb_list = []
    leagues = await get_leagues(sport_id)
    for league in leagues['leagues']:
        kb_list.append({sport_id + "+" + league['league_id']: league['league_name']})
    return kb_list


async def get_sports_list():
    response = await get_sports()  # Assuming get_sports is defined elsewhere and returns the sports dictionary
    sports = response['sports']  # This is now expected to be a list of dictionaries
    kb_lst = []
    if sports['code'] == 200:
        sport_data = sports['data']
    else:
        return False
    for sport_dict in sport_data:  # Iterating through each dictionary in the list
        for sport_id, details in sport_dict.items():  # Now getting sport_id and details
            kb_lst.append({sport_id: get_sport_emoji(details['SPORT_NAME']) + " " + details['SPORT_NAME']})
    return kb_lst


async def get_sports():
    result = await champions_api.get_sports()
    return result


async def get_leagues(sport_id):
    result = await champions_api.get_leagues(sport_id)
    return result


async def create_event_keyboard(event, sport_id, selected_market_key_name=None, continue_path='default'):
    markup = InlineKeyboardMarkup()
    event_data = event['event']['data']
    pprint(event_data)

    # Title and message
    title = await build_title_from_teams(event_data['teams'])
    msg = f"""🏆 *{title}* 🏆
    
📝 To place your bet:

*1. Pick a Market:* Choose the type of bet you want.
*2. Select a Choice:* After choosing a market, pick your bet from the options provided.

Happy betting! 🍀


"""

    # Determine the default market key if none is selected
    if selected_market_key_name is None and event_data['order_book']:
        selected_market_key_name = event_data['order_book'][0]['market_key_name']

    # First row for market keys with a "✔" for the selected one
    market_key_buttons = []
    for market in event_data['order_book']:
        txt = "✔" if market['market_key_name'] == selected_market_key_name else ""
        txt += market['market_key_name']
        market_key_buttons.append(InlineKeyboardButton(text=txt,
                                                       callback_data=f"sel_mk${ss.shorten(event_data['event_id'])}_{sport_id}_{ss.shorten(market['market_key_name'])}"))
    markup.row(*market_key_buttons)

    # Second row for the odds of the selected market key
    odds_buttons = []
    for market in event_data['order_book']:
        if market['market_key_name'] == selected_market_key_name:
            for odd in market['odds']:
                txt = f"{odd['rate']} - {odd['odd_name']}"
                callback_data = f"sel_odd${ss.shorten(event_data['event_id'])}_{sport_id}_{ss.shorten(selected_market_key_name)}_{odd['odd_id']}_{continue_path}"

                odds_buttons.append(InlineKeyboardButton(text=txt, callback_data=callback_data))
    markup.row(*odds_buttons)
    markup.row(InlineKeyboardButton(text=BACK_BUTTON, callback_data="back_to_start"))

    return markup, msg


async def view_event(callback_query: types.CallbackQuery, selection_id: str, send=False):
    sport_id = selection_id.split("+")[0]
    event_id = selection_id.split("+")[1]
    continue_path = selection_id.split("+")[2]
    event = await champions_api.get_event(sport_id, event_id)
    if event['event']['code'] != 200:
        return False
    markup, msg = await create_event_keyboard(event, sport_id, continue_path=continue_path)

    if send:
        await callback_query.message.answer(msg, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
    else:
        await callback_query.message.edit_text(msg, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)


async def view_bet(callback_query: types.CallbackQuery, selection_id: str, send=False):
    data = await local_storage.get_resource(selection_id)
    event_id = data['event_id']
    participant = data['participant']

    bet_time = unix_time_to_gmt_string(participant['bet_time'])
    market_key_id = participant['market_key_id']
    odd_name = participant['odd']['odd_name']
    rate = participant['odd']['rate']
    amount = participant['amount']
    wallet_type = participant['wallet_type']
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(text=BACK_BUTTON, callback_data="back_to_start"))

    msg = f"""
🧾 _{bet_time}_

• *Side:* {odd_name}
• *Market Key:* {market_key_id}
• *Size:* `{amount}` {wallet_type}
• *Rate:* `{rate}`

*Event ID:* `{event_id}`
"""

    await callback_query.message.edit_text(msg, reply_markup=markup, parse_mode=types.ParseMode.MARKDOWN)


async def place_bet(callback_query: types.CallbackQuery, place_bet_id, state):
    bet_info = await local_storage.get_resource(place_bet_id)
    odd = (await champions_api.get_odd(bet_info['event_id'], bet_info['sport_id'], bet_info['market_key_name'],
                                       bet_info['odd_id']))['odd']
    pprint(bet_info)
    print(type(bet_info))
    participant = {
        "user_id": str(callback_query.from_user.id),
        "wallet_type": bet_info['wallet_type'],
        "market_key_id": bet_info['market_key_name'],
        "odd": odd,
        "amount": bet_info['amount'],
        "bet_time": time.time()
    }
    load_size = 15
    msg = "*Placing Bet:* "
    await callback_query.message.edit_text(msg, parse_mode=ParseMode.MARKDOWN)
    for i in range(load_size):
        for j in range(load_size):
            if i % 2 == 0:
                load_text = "*" + str(int(100 * (i / load_size))) + "%*" + " ➿💸"
            else:
                load_text = "*" + str(int(100 * (i / load_size))) + "%*" + " 〰💸"

        current_msg = msg + load_text
        await callback_query.message.edit_text(current_msg, parse_mode=ParseMode.MARKDOWN)
        await asyncio.sleep(1)
    response = await champions_api.place_bet(participant, bet_info['event_id'], bet_info['sport_id'])
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(text=HOME_BUTTON, callback_data="back_to_start"))

    if response and response['response'] == 'success':
        confirmation_message = "✅ Your bet has been placed successfully!"
        await callback_query.message.edit_text(confirmation_message, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
        return True

    else:
        error_message = "❌ There was an issue placing your bet. Please try again."
        await callback_query.message.edit_text(error_message, parse_mode=ParseMode.MARKDOWN)
    return False
