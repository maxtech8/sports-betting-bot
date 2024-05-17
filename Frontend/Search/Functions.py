import time
from pprint import pprint

from aiogram import types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, ParseMode

from Database.LocalStorage import LocalStorage
from Gaming.Functions import create_event_keyboard, build_title_from_teams
from Search.SearchEngine import SearchEngine

se = SearchEngine()
local_storage = LocalStorage.get_instance()
search_data_expire_delta = 3600
search_data_expire_time = 0


async def search(bot, provider_api, inline_query: types.InlineQuery):
    events = []
    await get_search_data(provider_api)
    search_results = se.search(inline_query.query)
    for hit in search_results.body['hits']['hits']:
        events.append({'event': {'data': hit['_source']}})
    if events == []:
        results = [
            InlineQueryResultArticle(
                id='1',
                title="No Results",
                input_message_content=InputTextMessageContent(message_text=f"Could not finding matching events")
            )
        ]
        await bot.answer_inline_query(inline_query.id, results)
        return
    results = []
    for event in events:
        markup, msg = await create_event_keyboard(event,None)
        title = await build_title_from_teams(event['event']['data']['teams'])
        results.append(InlineQueryResultArticle(
            id=event['event']['data']['event_id'],
            title=title,
            input_message_content=InputTextMessageContent(message_text=msg,  parse_mode=ParseMode.MARKDOWN),
            reply_markup=markup
        ))
    await bot.answer_inline_query(inline_query.id, results)


async def get_search_data(provider_api):
    global search_data_expire_delta
    global search_data_expire_time

    if time.time() > search_data_expire_time:
        se.wipe_index()
        search_data = await provider_api.get_all_events()
        inplay_events = search_data['inplay_events']
        upcoming_events = search_data['upcoming_events']
        docs = inplay_events + upcoming_events
        se.set_data(docs)
        search_data_expire_time = time.time() + search_data_expire_delta
