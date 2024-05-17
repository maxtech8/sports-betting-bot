import asyncio

from APIs.SportsBookAPI.BetsAPI.BetsAPI import BetsAPI
from APIs.SportsBookAPI.TheOddsAPI.TheOddsAPI import TheOddsAPI
from Configurations import ConfigSingleton
from Logger.CustomLogger import CustomLogger


class SportBookAPI:
    def __init__(self):
        self.logger = CustomLogger.get_instance()
        self.sports_config = ConfigSingleton.ConfigSingleton.get_instance().get_sport_config()
        self.api_accessor = {"BetsAPI": BetsAPI(), "OddsAPI": TheOddsAPI()}
        #asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def _get_sport_id_by_sport_name(self, sport_id):
        return self.sports_config[sport_id]["API_SPORT_ID"]

    async def _get_api_instance_by_sport_id(self, sport_id):
        api_name = self.sports_config[sport_id]["API_NAME"]
        return self.api_accessor[api_name]

    async def get_upcoming_events(self, sport_id, day):
        api_instance = await self._get_api_instance_by_sport_id(sport_id)
        api_sport_id = await self._get_sport_id_by_sport_name(sport_id)
        res = await api_instance.get_upcoming_events(sport_id=api_sport_id, day=day)
        return res

    async def get_ended_events(self, sport_id, day):
        api_instance = await self._get_api_instance_by_sport_id(sport_id)
        sport_id = await self._get_sport_id_by_sport_name(sport_id)
        return await api_instance.get_ended_events(sport_id=sport_id, day=day, events_ids=None)

    async def get_inplay_events(self, sport_id):
        api_instance = await self._get_api_instance_by_sport_id(sport_id)
        sport_id = await self._get_sport_id_by_sport_name(sport_id)
        return await api_instance.get_inplay_events(sport_id=sport_id)

    async def get_event_by_event_id(self, sport_id, event_id):
        api_instance = await self._get_api_instance_by_sport_id(sport_id)
        return await api_instance.get_event_by_event_id(event_id=event_id)

    async def get_odds(self, sport_id, event_id):
        api_instance = await self._get_api_instance_by_sport_id(sport_id)
        return await api_instance.get_odds(event_id=event_id)

    async def get_local_sport_id_by_api_id(self, api_sport_id):
        for key, data in self.sports_config.items():
            if data['API_SPORT_ID'] == api_sport_id:
                return key
        return None

    async def get_event_odds(self, sport_id, event_id, sport_league_id=None):
        api_instance = await self._get_api_instance_by_sport_id(sport_id)
        return await api_instance.get_event_odds(event_id=event_id, sport_league_id=sport_league_id)
