import asyncio
import math
from enum import Enum
from pprint import pprint

import aiohttp

from APIs.Errors import Error
from APIs.SportsBookAPI.AbstractSportsBook import AbstractSportsBook
from Configurations.ConfigSingleton import ConfigSingleton
from Gaming.Event import TimeStatus, Event
from Gaming.League import League
from Gaming.MarketKey import MarketKey
from Gaming.MarketKey import MarketKeysMapping
from Gaming.Odd import Odd
from Gaming.Score import Score
from Gaming.Sport import Sport
from Gaming.Team import Team
from Utils.Utils import Utils


class MarketKeysMappingBetsAPI(Enum):
    _1_1 = MarketKeysMapping.FULL_TIME_RESULT.value
    _1_2 = MarketKeysMapping.ASIAN_HANDICAP.value
    _1_3 = MarketKeysMapping.GOAL_LINE.value
    _1_4 = MarketKeysMapping.ASIAN_CORNERS.value
    _1_5 = MarketKeysMapping.FIRST_HALF_ASIAN_HANDICAP.value
    _1_6 = MarketKeysMapping.FIRST_HALF_GOAL_LINE.value
    _1_7 = MarketKeysMapping.FIRST_HALF_ASIAN_CORNERS.value
    _1_8 = MarketKeysMapping.HALF_TIME_RESULT.value
    _18_1 = MarketKeysMapping.MONEY_LINE.value
    _18_2 = MarketKeysMapping.SPREAD.value
    _18_3 = MarketKeysMapping.TOTAL_POINTS.value
    _18_4 = MarketKeysMapping.MONEY_LINE_HALF.value
    _18_5 = MarketKeysMapping.SPREAD_HALF.value
    _18_6 = MarketKeysMapping.TOTAL_POINTS_HALF.value
    _18_7 = MarketKeysMapping.QUARTER_WINNER_2WAY.value
    _18_8 = MarketKeysMapping.QUARTER_HANDICAP.value
    _18_9 = MarketKeysMapping.QUARTER_TOTAL_2WAY.value
    _3_1 = MarketKeysMapping.MATCH_WINNER_2WAY.value
    _3_2 = MarketKeysMapping.ASIAN_HANDICAP_2.value
    _3_3 = MarketKeysMapping.OVER_UNDER.value
    _3_4 = MarketKeysMapping.DRAW_NO_BET_CRICKET.value


class TimeStatusMappingBetsAPI(Enum):
    _0 = TimeStatus.NOT_STARTED
    _1 = TimeStatus.IN_PLAY
    _2 = TimeStatus.TO_BE_FIXED
    _3 = TimeStatus.ENDED
    _4 = TimeStatus.POSTPONED
    _5 = TimeStatus.CANCELLED
    _6 = TimeStatus.WALKOVER
    _7 = TimeStatus.INTERRUPTED
    _8 = TimeStatus.ABANDONED
    _9 = TimeStatus.RETIRED
    _10 = TimeStatus.SUSPENDED
    _11 = TimeStatus.DECIDED_BY_FA
    _12 = TimeStatus.REMOVED


class BetsAPI(AbstractSportsBook):

    def __init__(self):
        super().__init__()
        self.config = ConfigSingleton.get_instance().get_private_keys()
        self.base_url = "https://api.b365api.com"
        self.api_key = self.config["betsapi_api_key"]
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def _interpret_events(self, events):
        interpreted_events = []
        for upcoming_event in events:
            event_result = await self._interpret_event(upcoming_event)
            if event_result is None:
                continue
            interpreted_events.append(event_result)
        return interpreted_events

    async def _get_sport_name_by_sport_id(self, sport_id):
        for sport_name, data in self.sports_config.items():
            if str(data['API_SPORT_ID']) == str(sport_id):
                return sport_name

    def get_scores_from_event(self, event):
        if 'ss' in event and event['ss']:
            # Detect delimiter and split the score string
            delimiter = '-' if '-' in event['ss'] else ','
            score_strings = event['ss'].split(delimiter)
            # Parse the scores using the regex to extract the run parts
            scores = [self.parse_score(s.strip()) for s in score_strings]
        else:
            scores = [None, None]  # If 'ss' is not present or empty, return None values

        return scores

    async def _interpret_event(self, event):
        scores = None
        if not ('away' in event.keys() or 'home' in event.keys()):
            self.logger.error(f"away or home not found in event. upcoming_event: {event}")
            return None
        teams = [Team(event['home']['id'], event['home']['name']), Team(event['away']['id'], event['away']['name'])]
        commence_time = event['time']
        sport_id = int(event['sport_id'])

        sport_name = await self._get_sport_name_by_sport_id(sport_id=sport_id)
        sport = Sport(sport_id, sport_name)
        # if not event['league']['id'] in SportsWithScores.sports_with_scores and event['league']['name'] not in SportsWithScores.sports_with_scores:
        #     print(event['league']['id'], event['league']['name'])
        #     return None
        league = League(event['league']['id'], event['league']['name'])
        time_status = TimeStatusMappingBetsAPI['_' + event['time_status']].value
        event_id = event['id']
        # print("!!!!!!!!!!!!")
        # print(self.get_scores_from_event(event['ss']))
        if 'ss' in event and event['ss']:
            if '-' in event['ss']:
                res = event['ss'].split('-')
            elif ',' in event['ss']:
                res = event['ss'].split(',')
            else:
                res = [event['ss'], '']

            for i, s in enumerate(res):
                if '/' in s:
                    res[i] = s.split("/")[0]
            scores = Score(
                [{"name": event['home']['name'], "score": res[0]}, {"name": event['away']['name'], "score": res[1]}])
        event = Event(teams=teams, commence_time=commence_time, sport=sport, league=league, time_status=time_status,
                      event_id=event_id)
        if scores:
            event.set_score(scores)
        return event

    async def get_upcoming_events(self, sport_id, day):

        error_json_message = {"status": "error", "code": Error.ERR_FAILED_TO_GET_UPCOMING_EVENTS.value,
                              "message": "Failed to get upcoming events"}
        upcoming_events = []
        try:
            for current_day in range(day):
                self.logger.debug(f"Upcoming Events for sport_id : {sport_id} and day : {current_day}")
                params = {'token': self.api_key, 'sport_id': sport_id, "day": Utils.get_utc_date(current_day)}
                # timeout = aiohttp.ClientTimeout(total=10)  # Adjust the timeout as needed
                async with aiohttp.ClientSession() as session:
                    res = await session.get(f'{self.base_url}/v3/events/upcoming', params=params)

                    if res.status != 200:
                        self.logger.error(f"Error from get_upcoming_events_with_pager {res}")
                        return error_json_message
                    response_json = await res.json()
                    pages = math.ceil(response_json['pager']['total'] / response_json['pager']['per_page'])
                    interpreted_upcoming_events = await self._interpret_events(response_json['results'])
                    if interpreted_upcoming_events is None:
                        return error_json_message
                    upcoming_events.extend(interpreted_upcoming_events)

                    for i in range(1, pages):
                        params['page'] = i + 1
                        res = await session.get(f'{self.base_url}/v3/events/upcoming', params=params)
                        response_json = await res.json()
                        interpreted_upcoming_events = await self._interpret_events(response_json['results'])
                        if interpreted_upcoming_events is None:
                            return error_json_message
                        upcoming_events.extend(interpreted_upcoming_events)

            return {
                "status": "success",
                "code": Error.SUCCESS.value,
                "data": [obj.to_dict() for obj in upcoming_events]
            }
        except Exception as ex:
            self.logger.error(f'error from get_upcoming_events ex: {ex}')
            return error_json_message

    async def get_odds(self, event_id):
        error_json_message = {
            "status": "error",
            "code": Error.ERR_FAILED_TO_GET_UPCOMING_EVENTS.value,
            "message": f"Failed to get odds for event: {event_id}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{self.base_url}/v2/event/odds',
                                       params={'token': self.api_key, 'event_id': event_id}) as response:
                    odds = await response.json()
                    if odds['success'] == 0:
                        self.logger.debug(f"Odds are: {odds}")

                    market_keys = []
                    odds_dict = odds["results"]["odds"]

                    for market_key_id in odds_dict.keys():
                        if not odds_dict[market_key_id]:  # Empty odds
                            continue

                        last_odds = odds_dict[market_key_id][0]
                        last_odds = await self._parse_odds(last_odds, market_key_id, event_id)
                        if last_odds is None:
                            continue

                        market_key = MarketKey(MarketKeysMappingBetsAPI['_' + market_key_id].value, last_odds)
                        market_keys.append(market_key)

                    return {"status": "success", "code": Error.SUCCESS.value,
                            "data": [obj.to_dict() for obj in market_keys]}

        except Exception as ex:
            self.logger.error(f'error from get_odds ex : {ex}')
            return error_json_message

    async def get_odd_name(self, event_id, odd_id):
        pass

    async def _parse_odds(self, odds, market_key_id, event_id):
        if market_key_id == "18_1" or market_key_id == "3_1":
            if odds['home_od'] == '-' or odds["away_od"] == '-':
                return None
            # TODO fix odd name: get_odd_name(self,event_id, odd_id):
            event = await self.get_event_by_event_id(event_id=event_id)
            if not event or event["code"] != 200:
                return None
            event = event["data"]
            home_team = event[0]["teams"][0]["team_name"]
            away_team = event[0]["teams"][1]["team_name"]
            odd_home = Odd(home_team, home_team, float(odds['home_od']))
            odd_away = Odd(away_team, away_team, float(odds['away_od']))
            return [odd_home, odd_away]
        else:
            print(f"No _prase_odds for odds: {odds}, market_key_id: {market_key_id}")
            self.logger.error(f"No _prase_odds for odds: {odds}, market_key_id: {market_key_id}")
        return None

    async def get_ended_events(self, sport_id, day, events_ids=None):
        day = Utils.get_utc_date()
        error_json_message = {"status": "error", "code": Error.ERR_FAILED_TO_GET_ENDED_EVENTS.value,
                              "message": "Failed to get ended events"}
        try:
            self.logger.debug(f"Ended Events for sport_id : {sport_id} and day : {day}")
            params = {'token': self.api_key, 'sport_id': sport_id, 'day': day, 'page': 1}

            async with aiohttp.ClientSession() as session:
                res = await session.get(f'{self.base_url}/v3/events/ended', params=params)
                if res.status != 200:
                    self.logger.error(f"Error from get_ended_events")
                    return error_json_message

                response_json = await res.json()
                pages = math.ceil(response_json['pager']['total'] / response_json['pager']['per_page'])
                all_results = []
                all_results.extend(response_json['results'])

                for i in range(1, pages):
                    self.logger.debug(f"page {i + 1}")
                    params['page'] = i + 1
                    try:
                        res = await session.get(f'{self.base_url}/v3/events/ended', params=params)
                        response_json = await res.json()
                        all_results.extend(response_json['results'])
                    except Exception as ex:
                        print(ex)
                        pass

                # return {"event_id": response["id"], "scores": response["scores"], "event": event.to_dict(),
                #         "completed": response["completed"]}
                interpreted_ended_events = await self._interpret_events(all_results)
                res = []
                for event in interpreted_ended_events:
                    try:
                        event_id = event.event_id
                        event_dict = event.to_dict()
                        completed = True
                        scores = event.get_score().to_dict()
                        parsed_scores = []
                        for score_team, score_res in scores.items():
                            parsed_scores.append({"name": score_team, "score": score_res})

                        res.append({"event_id": event_id, "scores": parsed_scores, "event": event_dict,
                                    "completed": completed})
                    except Exception as ex:
                        self.logger.error(f'BetsAPI : Error from get_ended_events ex : {ex}')
                    finally:
                        continue
                return {
                    "status": "success",
                    "code": Error.SUCCESS.value,
                    "data": res
                }
        except Exception as ex:
            self.logger.error(f'error from get_ended_events ex : {ex}')
            return error_json_message

    async def _parse_ended_event(self, event):
        event_id = event["id"]

    async def get_inplay_events(self, sport_id):
        error_json_message = {
            "status": "error",
            "code": Error.ERR_FAILED_TO_GET_INPLAY_EVENTS.value,
            "message": "Failed to get inplay events"
        }
        try:
            self.logger.debug(f"Inplay Events for sport_id : {sport_id}")
            params = {'token': self.api_key, 'sport_id': sport_id}

            async with aiohttp.ClientSession() as session:
                res = await session.get(f'{self.base_url}/v3/events/inplay', params=params)
                response_json = await res.json()

                if response_json['success'] != 1:
                    self.logger.error(f"Error from get_inplay_events")
                    return error_json_message

                inplay_events = response_json['results']
                interpreted_inplay_events = await self._interpret_events(inplay_events)

                if interpreted_inplay_events is None:
                    return error_json_message

                interpreted_inplay_events = [obj.to_dict() for obj in interpreted_inplay_events]
                return {
                    "status": "success",
                    "code": Error.SUCCESS.value,
                    "data": interpreted_inplay_events
                }
        except Exception as ex:
            print(f"Error from get_inplay_events, ex : {ex}")
            self.logger.error(f'Error from get_inplay_events, ex : {ex}')
            return error_json_message

    async def get_event_by_event_id(self, event_id):
        error_json_message = {
            "status": "error",
            "code": Error.ERR_FAILED_TO_GET_VIEW_EVENT.value,
            "message": f"Failed to view event id: {event_id}"
        }

        try:
            self.logger.debug(f"View Event by event_id : {event_id}")
            params = {'token': self.api_key, 'event_id': event_id}

            async with aiohttp.ClientSession() as session:
                res = await session.get(f'{self.base_url}/v1/event/view', params=params)
                if res.status != 200:
                    self.logger.error(f"Error from get_view_event_by_event_id")
                    return error_json_message

                response_json = await res.json()
                event = response_json['results']
                interpreted_event = await self._interpret_events(event)

                if interpreted_event is None:
                    return error_json_message

                interpreted_event = [obj.to_dict() for obj in interpreted_event]
                return {
                    "status": "success",
                    "code": Error.SUCCESS.value,
                    "data": interpreted_event
                }
        except Exception as ex:
            self.logger.error(f'Error from get_view_event, event_id: {event_id},  ex : {ex}')
            return error_json_message

    # def local_id_to_api_id(self, local_id):
    #     local_id = str(local_id)
    #     for sport_id, data in self.sports_config.items():
    #         if sport_id == local_id:
    #             return str(data['API_SPORT_ID'])
    #         return None  # or some error handling
    #
    # # Function to convert from API ID to local ID
    # def api_id_to_local_id(self, api_id):
    #     for sport_id, data in self.sports_config.items():
    #         if str(data['API_SPORT_ID']) == str(api_id):
    #             return sport_id
    #         return None  # or some error handling

    async def get_event_odds(self, event_id, sport_league_id):
        res = await self.get_odds(event_id)
        if res["code"] != 200:
            self.logger.error(f"No event odds for event_id: {event_id}")
            return None
        ret = {}
        markets = res["data"]
        for market in markets:
            market_key = market["market_key_name"]
            odds = []
            for odd in market["odds"]:
                odd_id = odd["odd_id"]
                odd_name = odd["odd_name"]
                rate = odd["rate"]
                odds.append(Odd(odd_id=odd_id, odd_name=odd_name, rate=rate))
            ret[market_key] = odds
        return ret

        # res = {}
        # bookmakers = response["bookmakers"]
        # markets = bookmakers[0]["markets"]
        # for market in markets:
        #     market_key = market["key"]
        #     global_market_key = MarketKeysMappingTheOddsAPI[market_key].value
        #     outcomes = market["outcomes"]
        #     odds = []
        #     for outcome in outcomes:
        #         odd_id = odd_name = outcome["name"]
        #         rate = outcome["price"]
        #         odds.append(Odd(odd_id=odd_id, odd_name=odd_name, rate=rate))
        #     res[global_market_key] = odds
        # return res
