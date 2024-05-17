import asyncio
import math
import time
from datetime import datetime
from enum import Enum
from pprint import pprint

import aiohttp
import requests

from APIs.Errors import Error
from APIs.SportsBookAPI.AbstractSportsBook import AbstractSportsBook
from APIs.SportsBookAPI.TheOddsAPI import SportsWithScores
from Configurations.ConfigSingleton import ConfigSingleton
from Gaming.Event import TimeStatus, Event
from Gaming.League import League
from Gaming.MarketKey import MarketKey
from Gaming.MarketKey import MarketKeysMapping
from Gaming.Odd import Odd
from Gaming.Sport import Sport
from Gaming.Team import Team
from Utils.Utils import Utils


class MarketKeysMappingTheOddsAPI(Enum):
    h2h = MarketKeysMapping.FULL_TIME_RESULT.value


class TheOddsAPI(AbstractSportsBook):

    def __init__(self):
        super().__init__()
        self.config = ConfigSingleton.get_instance().get_private_keys()
        self.base_url = "https://api.the-odds-api.com"
        self.api_key = self.config["oddsapi_api_key"]
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        self.upcoming_and_inplay_events = []
        self.sports, self.leagues = None, None
        self.inplay_events, self.upcoming_events = {}, {}
        self.last_refresh_event_time = None
        self.last_refresh_event_times = {}
        self.is_initallized = False

    async def _init(self):
        if not self.is_initallized:
            await self._get_sports_odds_api()
            self.is_initallized = True

    async def _interpret_sport_odds_api(self, response):
        sports = {}
        leagues = {}
        for sport_in_dict in response:
            league_id = sport_in_dict['key']
            league_name = sport_in_dict["title"]
            sport_name = sport_in_dict["group"]
            sport_id = sport_in_dict["group"]
            league = League(league_id=league_id, league_name=league_name)
            sport = Sport(sport_id=sport_id, sport_name=sport_name)
            if sport_id not in sports.keys():
                sports[sport_id] = sport
            if sport_id not in leagues.keys():
                leagues[sport_id] = {league_id: league}
            else:
                if league_id not in leagues[sport_id].keys():
                    leagues[sport_id][league_id] = league
        return sports, leagues

    async def _get_sports_odds_api(self):
        try:
            async with aiohttp.ClientSession() as session:
                response = await session.get(f'{self.base_url}/v4/sports',
                                             params={'apiKey': self.api_key})
                if response.status != 200:
                    return None
                response_json = await response.json()
                self.sports, self.leagues = await self._interpret_sport_odds_api(response_json)
                for sport_name in self.sports.keys():
                    self.last_refresh_event_times[sport_name] = None


        except Exception as ex:
            self.logger.error(f"Unable to fetch get_sport_odds_api, ex: {ex}")

    async def _get_odds_odds_api_per_sport(self, sport_name) -> bool:
        if sport_name not in self.leagues.keys():
            return False  # ERR
        leagues = self.leagues[sport_name].keys()
        self.upcoming_events[sport_name] = []
        self.inplay_events[sport_name] = []

        tasks = [self._get_odds_odds_api_per_league(sport_name=sport_name, sport_league=league_id) for league_id in
                 leagues if league_id in SportsWithScores.sports_with_scores]
        await asyncio.gather(*tasks)
        return True  # SUCCESS

    async def _get_odds_odds_api_per_league(self, sport_name, sport_league):
        try:
            async with (aiohttp.ClientSession() as session):
                await asyncio.sleep(5)
                params = {'apiKey': self.api_key, 'regions': 'us', 'dateFormat': 'unix'}

                response = await session.get(f'{self.base_url}/v4/sports/{sport_league}/odds', params=params)
                if response.status != 200:
                    return None
                response_json = await response.json()
                inplay_events, upcoming_events = await self._parse_odds_odds_api(response_json)
                if inplay_events is None or upcoming_events is None:
                    return

                if sport_name not in self.upcoming_events.keys():
                    self.upcoming_events[sport_name] = upcoming_events
                else:
                    self.upcoming_events[sport_name].extend(upcoming_events)
                if sport_name not in self.inplay_events.keys():
                    self.inplay_events[sport_name] = inplay_events
                else:
                    self.inplay_events[sport_name].extend(inplay_events)
        except Exception as ex:
            self.logger.error(f"Unable to fetch _get_odds_odds_api, ex: {ex}")

    async def _convert_to_timestamp(self, date_string):
        dt = datetime.fromisoformat(date_string)
        return dt.timestamp()

    async def _find_sport_id_by_league_id(self, league_id):
        for _sport_id in self.leagues.keys():
            if league_id in self.leagues[_sport_id].keys():
                return _sport_id
        return None

    async def _find_league_name_by_sport_id(self, sport_id, league_id):
        return self.leagues[sport_id][league_id].league_name

    async def _parse_odds_odds_api(self, odds_response):
        try:
            upcoming_events, inplay_events = [], []
            for event in odds_response:
                event_id = event["id"]
                league_id = event["sport_key"]
                commence_time = event["commence_time"]
                home_team = event["home_team"]
                away_team = event["away_team"]
                home_team = Team(team_id=home_team, team_name=home_team)
                away_team = Team(team_id=away_team, team_name=away_team)
                teams = [home_team, away_team]
                curr_time = time.time()
                if curr_time >= commence_time:
                    time_status = TimeStatus.IN_PLAY
                else:
                    time_status = TimeStatus.NOT_STARTED
                sport_id = await self._find_sport_id_by_league_id(league_id)
                sport = Sport(sport_id=sport_id, sport_name=sport_id)
                league_name = await self._find_league_name_by_sport_id(sport_id=sport_id, league_id=league_id)
                league = League(league_id=league_id, league_name=league_name)
                if not "bookmakers" in event or not event["bookmakers"]:
                    self.logger.error(
                        f"Error, no bookmakers for event {event_id}, Probably nothing to do with this error (bug from the API)")
                    return None, None
                book_makers = event["bookmakers"][0]
                if not book_makers:
                    self.logger.error(f"Error with _parse_odds_odds_api, no bookmakers for event_id: {event_id}")
                    return None, None
                markets = book_makers["markets"]
                if not markets:
                    return None, None
                market_keys = []
                for market in markets:
                    market_key_name = market["key"] # h2h ->
                    odds = []
                    for outcome in market["outcomes"]:
                        odd_id = odd_name = outcome["name"]
                        rate = outcome["price"]
                        odds.append(Odd(odd_id=odd_id, odd_name=odd_name, rate=rate))

                    market_keys.append(MarketKey(market_key_name=MarketKeysMappingTheOddsAPI[market_key_name].value, odds=odds))
                event = Event(teams=teams, commence_time=commence_time, sport=sport, league=league, event_id=event_id,
                              time_status=time_status)
                event.set_order_book(market_keys)
                if time_status == TimeStatus.IN_PLAY:
                    inplay_events.append({event_id: event})
                else:
                    upcoming_events.append({event_id: event})
            return inplay_events, upcoming_events
        except Exception as ex:
            self.logger.warning(f"Exception {ex} from TheOddsApi, probably no market_key_name handled named:{market_key_name}")

    async def get_upcoming_events(self, sport_id, day):
        await self._init()
        error_message = {
            "status": "error",
            "code": Error.ERR_FAILED_TO_GET_UPCOMING_EVENTS.value,
            "message": f"Failed to get upcoming_event, sport_name: {sport_id}, day: {day}"
        }
        refresh_time = self.prj_config["SpecificAPIParams"]["OddsAPI"][sport_id]["UpcomingEventsRefreshTimeInSeconds"]
        res = await self._refresh_odds(sport_id, refresh_time)
        if not res:
            self.logger.warning(f"Failed to get_upcoming_events for sport_id: {sport_id}, day: {day}")
            return error_message
        # date_object = datetime.strptime(day, '%Y%m%d').date()

        if self.upcoming_events is None or sport_id not in self.upcoming_events.keys():
            return {
                "status": "error",
                "code": Error.ERR_FAILED_TO_GET_UPCOMING_EVENTS.value,
                "message": f"Failed to get upcoming_event, sport_name: {sport_id}, day: {day}"
            }
        desired_day_upcoming_events = []
        for event in self.upcoming_events[sport_id]:
            event_obj = list(event.values())[0]
            desired_day_upcoming_events.append(event_obj)
        return {
            "status": "success",
            "code": Error.SUCCESS.value,
            "data": [obj.to_dict() for obj in desired_day_upcoming_events]
        }

    async def tokenize_events_ids(self, event_ids_lst):
        if event_ids_lst is None:
            return ""
        tokenized_events_ids = ""
        for index, event_id in enumerate(event_ids_lst):
            if index == 0:
                tokenized_events_ids += str(event_id)
            else:
                tokenized_events_ids += ',' + str(event_id)
        return tokenized_events_ids

    async def _get_ended_events(self, sport_id, day, event_ids=None):
        scored_events = []
        if sport_id not in self.leagues.keys():
            return None  # ERR
        leagues = self.leagues[sport_id].keys()
        tasks = [self._get_ended_events_odds_api_per_league(sport_league=league_id, day=day, event_ids=event_ids) for
                 league_id in
                 leagues]
        results = await asyncio.gather(*tasks)
        for result in results:
            if result:
                scored_events.extend(result)
        return scored_events

    async def _parse_odds(self, response):
        pass

    async def _parse_ended_events(self, response):
        event_id = response["id"]
        league_id = response["sport_key"]
        commence_time = response["commence_time"]
        home_team = response["home_team"]
        away_team = response["away_team"]
        home_team = Team(team_id=home_team, team_name=home_team)
        away_team = Team(team_id=away_team, team_name=away_team)
        teams = [home_team, away_team]
        sport_id = await self._find_sport_id_by_league_id(league_id)
        sport = Sport(sport_id=sport_id, sport_name=sport_id)
        league_name = await self._find_league_name_by_sport_id(sport_id=sport_id, league_id=league_id)
        league = League(league_id=league_id, league_name=league_name)
        event = Event(teams=teams, commence_time=commence_time, sport=sport, league=league, event_id=event_id,
                      time_status=TimeStatus.TO_BE_FIXED)

        return {"event_id": response["id"], "scores": response["scores"], "event": event.to_dict(),
                "completed": response["completed"]}

    async def _get_ended_events_odds_api_per_league(self, sport_league, day, event_ids=None):
        try:
            tokenized_events_ids = await self.tokenize_events_ids(event_ids)
            await asyncio.sleep(10)  # This sleep comes to prevets "too many requests" error response from odds api
            async with aiohttp.ClientSession() as session:
                if not tokenized_events_ids:
                    response = await session.get(f'{self.base_url}/v4/sports/{sport_league}/scores/',
                                                 params={'apiKey': self.api_key, 'dateFormat': 'unix',
                                                         'daysFrom': day})
                else:
                    response = await session.get(f'{self.base_url}/v4/sports/{sport_league}/scores/',
                                                 params={'apiKey': self.api_key, 'dateFormat': 'unix',
                                                         'daysFrom': day, 'eventIds': tokenized_events_ids})
                if response.status != 200:
                    self.logger.warning(
                        f"error while getting ended events from odds api, sport_league: {sport_league}, day: {day}, event_ids: {event_ids}, response reason: {response.reason}, Probably nothing to do with it except another sleep")
                    return None
                response_json = await response.json()
                tasks = [self._parse_ended_events(event) for event in response_json if event["scores"] is not None]
                results = await asyncio.gather(*tasks)
                return results
        except Exception as ex:
            self.logger.error(
                f"error while getting ended events from odds api, sport_league: {sport_league}, day: {day}, event_ids: {event_ids}, ex: {ex}")
            return None

    async def get_ended_events(self, sport_id, day, events_ids=None):
        error_message = {
            "status": "error",
            "code": Error.ERR_FAILED_TO_GET_ENDED_EVENTS.value,
            "message": f"Failed to get ended_events, sport_name: {sport_id}"
        }
        await self._init()
        response = await self._get_ended_events(sport_id, day)
        if not response:
            self.logger.error(f"Failed to get ended_events, sport_name: {sport_id}, the response is: {response}, and if the response is empty, probably no ended games for this sport_name")
            return error_message
        return {
            "status": "success",
            "code": Error.SUCCESS.value,
            "data": response
        }

    async def _refresh_odds(self, sport_id, refresh_time):
        curr_time = time.time()
        if self.last_refresh_event_times[sport_id] is None or curr_time - self.last_refresh_event_times[
            sport_id] >= refresh_time:
            res = await self._get_odds_odds_api_per_sport(sport_id)  # Need to check if None
            if not res:
                return False
            self.last_refresh_event_times[sport_id] = curr_time
        return True

    async def get_inplay_events(self, sport_id):
        await self._init()

        error_message = {
            "status": "error",
            "code": Error.ERR_FAILED_TO_GET_INPLAY_EVENTS.value,
            "message": f"Failed to get upcoming_event, sport_name: {sport_id}"
        }
        refresh_time = self.prj_config["SpecificAPIParams"]["OddsAPI"][sport_id]["InplayEventsRefreshTimeInSeconds"]
        if not await self._refresh_odds(sport_id, refresh_time):
            return error_message

        if self.inplay_events is None or sport_id not in self.inplay_events.keys():
            return error_message
        result = [value for event in self.inplay_events[sport_id] for key, value in event.items()]

        return {
            "status": "success",
            "code": Error.SUCCESS.value,
            "data": [obj.to_dict() for obj in result]
        }

    # async def get_event_odds(self, event_id):

    async def get_event_by_event_id(self, event_id):
        await self._init()

        error_message = {
            "status": "error",
            "code": Error.ERR_FAILED_TO_GET_VIEW_EVENT.value,
            "message": f"Error from get_event_by_event_id, event_id: {event_id}"
        }
        sport_id_founded = None
        is_inplay_event = False
        for sport_id in self.upcoming_events.keys():
            for event in self.upcoming_events[sport_id]:
                event_obj = list(event.values())[0]
                if event_obj.event_id == event_id:
                    sport_id_founded = sport_id
        if sport_id_founded is None:
            for sport_id in self.inplay_events.keys():
                for event in self.inplay_events[sport_id]:
                    event_obj = list(event.values())[0]
                    if event_obj.event_id == event_id:
                        sport_id_founded = sport_id
                        is_inplay_event = True

        if sport_id_founded is None:
            self.logger.error(f"Error from get_event_by_event_id, event_id: {event_id}")
            return error_message
        if is_inplay_event:
            refresh_time = self.prj_config["SpecificAPIParams"]["OddsAPI"][sport_id_founded][
                "InplayEventsRefreshTimeInSeconds"]
        else:
            refresh_time = self.prj_config["SpecificAPIParams"]["OddsAPI"][sport_id_founded][
                "UpcomingEventsRefreshTimeInSeconds"]
        if not await self._refresh_odds(sport_id_founded, refresh_time):
            return error_message
        result = [value for event in self.inplay_events[sport_id_founded] for key, value in event.items()]

        if is_inplay_event:
            return {
                "status": "success",
                "code": Error.SUCCESS.value,
                "data": [obj.to_dict() for obj in result]
            }

    # Need to return the specific event. Consider to change the events like upcoming_events[sport_id][event_id] for better search

    async def get_odds(self, event_id):
        for sport_name in self.upcoming_events:
            for event in self.upcoming_events[sport_name]:
                event_obj_id = list(event.keys())[0]
                if event_id == event_obj_id:
                    return {
                        "status": "success",
                        "code": Error.SUCCESS.value,
                        "data": [market_key.to_dict() for market_key in event[event_obj_id].get_order_book()]
                    }
        for sport_name in self.inplay_events:
            for event in self.inplay_events[sport_name]:
                event_obj_id = list(event.keys())[0]
                if event_id == event_obj_id:
                    return {
                        "status": "success",
                        "code": Error.SUCCESS.value,
                        "data": [market_key.to_dict() for market_key in event[event_obj_id].get_order_book()]
                    }
        return {
            "status": "success",
            "code": Error.SUCCESS.value,
            "data": []
        }


    async def parse_odd(self, response):
        res = {}
        bookmakers = response["bookmakers"]
        markets = bookmakers[0]["markets"]
        for market in markets:
            market_key = market["key"]
            global_market_key = MarketKeysMappingTheOddsAPI[market_key].value
            outcomes = market["outcomes"]
            odds = []
            for outcome in outcomes:
                odd_id = odd_name = outcome["name"]
                rate = outcome["price"]
                odds.append(Odd(odd_id=odd_id, odd_name=odd_name, rate=rate))
            res[global_market_key] = odds
        return res


        # if not market:
        #     self.logger.error(f"No market in resepone {response}")
        #     return None


    async def get_event_odds(self, event_id, sport_league_id):
        try:
            async with aiohttp.ClientSession() as session:
                await asyncio.sleep(10)
                response = await session.get(f'{self.base_url}/v4/sports/{sport_league_id}/events/{event_id}/odds',
                                                 params={'apiKey': self.api_key, 'regions': 'us'})
                if response.status != 200:
                    self.logger.error(
                        f"error while getting event odds from the odds api, sport_league: {sport_league_id}, event_id: {event_id}, response reason: {response.reason}")
                    return None
                response_json = await response.json()
                odds = await self.parse_odd(response_json)
                if not odds:
                    self.logger.error(f"error while getting event odds from the odds api, sport_league: {sport_league_id}, event_id: {event_id}")
                    return None
                return odds
        except Exception as ex:
            self.logger.error(
                f"error while getting event odds from the odds api, sport_league: {sport_league_id}, event_id: {event_id}, ex: {ex}")
            return None
