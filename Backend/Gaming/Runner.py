import asyncio
import time
from pprint import pprint

from APIs.Errors import Error
from APIs.SportsBookAPI.SportBookAPI import SportBookAPI
from Configurations import ConfigSingleton
from Databases.Remote.Firebase.Firebase import Firebase
from Gaming.Event import Event, TimeStatus
from Gaming.League import League
from Gaming.MarketKey import MarketKey
from Gaming.Odd import Odd
from Gaming.Participant import Participant
from Gaming.Score import Score
from Gaming.Sport import Sport
from Gaming.Team import Team
from Logger.CustomLogger import CustomLogger
from Pool.PoolFactory import PoolFactory
from Wallets.WalletTypes import WalletTypes, get_wallet_type
from Wallets.WalletsManagerSingleton import WalletsManagerSingleton


class Runner:

    def __init__(self):
        self._logger = CustomLogger.get_instance()
        self._sports_config = ConfigSingleton.ConfigSingleton.get_instance().get_sport_config()
        self._prj_config = ConfigSingleton.ConfigSingleton.get_instance().get_prjConfig()
        self._sport_book_api = SportBookAPI()
        self.participants_manager = {}
        self.history_participants = {}
        self.events_with_participants = {}
        self.active_sports = None  #
        self._upcoming_events = None  #
        self._inplay_events = None
        self.saved_events = []
        self.wallet_manager = WalletsManagerSingleton.get_instance()
        self.db = None

    async def _init_db(self):
        chosen_db = self._prj_config["DataBase"]
        if chosen_db == "Firebase":
            self.db = Firebase.get_instance()
        else:
            self._logger(f"Not exist database chosen: {chosen_db}")
            raise AssertionError(f"Not exist database chosen {chosen_db}")
        await self._load_db()

    async def _load_participants(self):
        res = await self.db.get({"path": "ParticipantsManager", "isCollection": True})
        try:
            for event_id, event_pariticipants in res.items():
                participants = []
                history_participants = []

                CompletedWithPrizes = event_pariticipants["CompletedWithPrizes"]

                # if CompletedWithPrizes:
                #     continue

                for participant in event_pariticipants["Participants"]:
                    amount = participant["amount"]
                    bet_time = participant["bet_time"]
                    market_key_id = participant["market_key_id"]
                    odd_id = participant["odd"]["odd_id"]
                    odd_name = participant["odd"]["odd_name"]
                    odd_rate = participant["odd"]["rate"]
                    odd_update_time = participant["odd"]["update_time"]
                    odd = Odd(odd_id=odd_id, odd_name=odd_name, rate=odd_rate, update_time=odd_update_time)
                    user_id = participant["user_id"]
                    wallet_type = WalletTypes(participant["wallet_type"])
                    part_obj = Participant(amount=amount, bet_time=bet_time, market_key_id=market_key_id, odd=odd,
                                           user_id=user_id, wallet_type=wallet_type)

                    if CompletedWithPrizes:
                        history_participants.append(part_obj)
                    else:
                        participants.append(part_obj)

                if CompletedWithPrizes:
                    self.history_participants[event_id] = history_participants
                else:
                    self.participants_manager[event_id] = participants


        except Exception as ex:
            self._logger.error(f"failed to load participants, ex: {ex}")

    async def _load_db(self):
        await self._load_participants()

    async def _init(self):
        # await asyncio.sleep(10)
        await self._init_db()
        self.pool = await PoolFactory.create_pool()
        self.active_sports = await self.get_active_sports()

        task = asyncio.create_task(self.wallet_manager.transactions_monitor())
        
        if self.active_sports['code'] == 200:
            self.active_sports = self.active_sports['data']
        else:
            self.active_sports = None
            return False

        upcoming_interval = self._prj_config["UpcomingEventsReloadIntervalTimeInSeconds"]
        inplay_interval = self._prj_config["InplayEventsReloadIntervalTimeInSeconds"]
        scored_interval = self._prj_config["ScoredEventsReloadIntervalTimeInSeconds"]

        while True:
            await asyncio.gather(
                self.timed_task(self._fetch_upcoming_events, upcoming_interval),
                self.timed_task(self._fetch_inplay_events, inplay_interval),
                self.timed_task(self._fetch_scored_events, scored_interval)
            )
        
    async def timed_task(self, task, interval):
        await task()  # Execute the task
        await asyncio.sleep(interval)  # Wait for the specified interval

    async def get_played_sports(self):
        try:
            active_sports = await self.get_active_sports()
            if active_sports["code"] != 200:
                return {"status": "error", "code": Error.ERR_FAILED_TO_PARSE_UPCOMING_EVENTS.value,
                        "message": "Failed to get played sports"}
            active_sports = active_sports["data"]
            gamed_sports = []
            for sport in active_sports:
                for sport_id, data in sport.items():
                    is_games_exists = True if len(self._upcoming_events[sport_id]) > 0 or len(
                        self._inplay_events[sport_id]) > 0 else False
                    if is_games_exists:
                        gamed_sports.append({sport_id: data})

            return {
                "status": "success",
                "code": Error.SUCCESS.value,
                "data": gamed_sports
            }
        except Exception as ex:
            self._logger.error(f"Probably self._upcoming[sport_id] is empty from get_played_sports, ex: {ex}")

    async def get_active_sports(self):
        try:
            active_sports = []
            for sport_id, data in self._sports_config.items():
                if "STATUS" in data and data["STATUS"] == "ON":
                    active_sports.append({sport_id: data})

            return {
                "status": "success",
                "code": Error.SUCCESS.value,
                "data": active_sports
            }
        except Exception as ex:
            self._logger.error(f"Probably self._upcoming[sport_id] is empty from get_active_sports, ex: {ex}")

    async def _parse_event(self, event, sport_id):
        curr_event = await self._simplify_parse_event(event)
        # teams = []
        #
        # for team in event["teams"]:
        #     teams.append(Team(team_id=team["team_id"], team_name=team["team_name"]))
        # league = League(league_id=event['league']['league_id'],
        #                 league_name=event['league']['league_name'])
        # sport_id = await self._sport_book_api.get_local_sport_id_by_api_id(event["sport"]["sport_id"])
        # sport = Sport(sport_id=sport_id,
        #               sport_name=event["sport"]["sport_name"])
        # curr_event = Event(commence_time=event['commence_time'], league=league, sport=sport,
        #                    event_id=event['event_id'], teams=teams,
        #                    time_status=TimeStatus(event["time_status"]))

        curr_event_order_book = await self._get_order_book_of_event(sport_id=sport_id, event=curr_event)
        if not curr_event_order_book:
            return None
        curr_event.set_order_book(curr_event_order_book)

        return curr_event

    async def _certain_sport_loading_upcoming_events(self, sport_id):
        sport_upcoming_events_result = await self._sport_book_api.get_upcoming_events(sport_id=sport_id,
                                                                                      day=3)

        if sport_upcoming_events_result["code"] != 200:
            self._logger.error(f"Failed to get some of the upcoming events, sport_id: {sport_id}")
            return []
        tasks = [self._parse_event(event=upcoming_event, sport_id=sport_id) for upcoming_event in
                 sport_upcoming_events_result['data']]
        sport_upcoming_events = await asyncio.gather(*tasks)
        return sport_upcoming_events

    async def _certain_sport_loading_inplay_events(self, sport_id):
        sport_inplay_events_result = await self._sport_book_api.get_inplay_events(sport_id=sport_id)

        if sport_inplay_events_result["code"] != 200:
            self._logger.error(f"Failed to get some of the inplay events, sport_id: {sport_id}")
            return []
        tasks = [self._parse_event(event=inplay_event, sport_id=sport_id) for inplay_event in
                 sport_inplay_events_result['data']]
        sport_inplay_events = await asyncio.gather(*tasks)
        return sport_inplay_events

    async def _fetch_scored_events(self):
        print("_fetch_scored_events")
        scored_events = {}
        sport_ids = []
        for sport_dict in self.active_sports:
            for sport_id, details in sport_dict.items():  # Now getting sport_id and details
                sport_ids.append(sport_id)
        tasks = [self._sport_book_api.get_ended_events(sport_id=sport_id, day=1) for sport_id in sport_ids]
        results = await asyncio.gather(*tasks)
        for result in results:
            if result["code"] == 200:
                for event in result["data"]:
                    event_id = event["event_id"]
                    scored_events[event_id] = event
        await self._update_participated_games(scored_events=scored_events)

    async def _simplify_parse_event(self, event):
        teams = []

        for team in event["teams"]:
            teams.append(Team(team_id=team["team_id"], team_name=team["team_name"]))
        league = League(league_id=event['league']['league_id'],
                        league_name=event['league']['league_name'])
        sport_id = await self._sport_book_api.get_local_sport_id_by_api_id(event["sport"]["sport_id"])
        sport = Sport(sport_id=sport_id,
                      sport_name=event["sport"]["sport_name"])
        curr_event = Event(commence_time=event['commence_time'], league=league, sport=sport,
                           event_id=event['event_id'], teams=teams,
                           time_status=TimeStatus(event["time_status"]))
        return curr_event

    async def handle_ended_events(self, event: Event):
        try:
            event_id = event.event_id
            participants = self.participants_manager[event_id]

            for participant in participants:
                winner_name = None
                amount = participant.amount
                market_key_id = participant.market_key_id
                odd_id = participant.odd.odd_id
                odd_name = participant.odd.odd_name
                rate = participant.odd.rate
                market_key = MarketKey(market_key_id, [Odd(odd_id=odd_id, odd_name=odd_name, rate=rate)])
                if market_key_id == market_key.market_key_name:
                    winner_name = market_key.get_winner(event.get_score().to_dict())
                if winner_name is None:
                    raise Exception("No winner ?! ")
                if winner_name == odd_id:
                    user_id = participant.user_id
                    wallet_type = participant.wallet_type
                    await self.pool.request_payment_from_pool(user_id=user_id, wallet_type=wallet_type,
                                                            amount=amount * rate)
                else:
                    # TODO give some messsage that the user is loosed
                    pass

            # Everything succeed
            self.history_participants[event_id] = self.participants_manager[event_id]
            del self.participants_manager[event_id]

            # maybe delete also from self.events_with_participants

            await self.db.update({"path": f"ParticipantsManager/{event_id}",
                                "data": {"CompletedWithPrizes": True}})
        except Exception as ex:
            print(f"handle_ended_events ex {ex}")
        

    async def _update_participated_games(self, scored_events):
        print(f"_fetch_scored_events -> _update_participated_games")
        # for event_id, event in self.events_with_participants.items():
        for event_id, event_dict, in scored_events.items():
            if event_id in self.participants_manager.keys():  # this event has participants
                if event_id in self.events_with_participants.keys():
                    self.events_with_participants[event_id].set_score(Score(event_dict["scores"]))
                else:
                    parsed_event = await self._simplify_parse_event(event_dict["event"])
                    parsed_event.set_score(Score(scored_events[event_id]["scores"]))
                    self.events_with_participants[event_id] = parsed_event
                self.events_with_participants[event_id].set_participants(self.participants_manager[event_id],
                                                                         override=True)
                # pprint(f"event_dic {event_dict}")
                if event_dict["completed"]:  # notify maybe in participants manager
                    # self.events_with_participants[event_id].notify_to_client()
                    await self.handle_ended_events(self.events_with_participants[event_id])

                    # await self.notify_end_game(self.events_with_participants[event_id]) # currently this line not implmented, in the future uncomment it to send message to the client

        # if self._upcoming_events:
        #     for evnt_id, scr_evnt in scored_events.items():
        #
        #         for sport_id in self._upcoming_events.keys():
        #             if evnt_id in self._upcoming_events[sport_id].keys():
        #                 self._upcoming_events[sport_id][evnt_id].set_score(Score(scr_evnt["scores"]))
        #                 raise Exception("Upcoming events with score ?! this is possible ?!")
        #             else:
        #                 pass
        #                 # TODO:
        #                 # In this case we probably need to fetch this event from the DB.
        #                 # This event not in inplay_events and not in upcoming_events but probably this event is
        #                 # already did in the past, so we need to try to bring it from db. if it doesnt exists in db this is weird.
        # if self._inplay_events:
        #     for evnt_id, scr_evnt in scored_events.items():
        #         for sport_id in self._inplay_events.keys():
        #             if evnt_id in self._inplay_events[sport_id].keys():
        #                 self._inplay_events[sport_id][evnt_id].set_score(Score(scr_evnt["scores"]))
        #             else:
        #                 pass
        #                 #self._logger.error(f"For some reason event_id {evnt_id} not in upcoming events")
        #                 # TODO:
        #                 # In this case we probably need to fetch this event from the DB.
        #                 # This event not in inplay_events and not in upcoming_events but probably this event is
        #                 # already did in the past, so we need to try to bring it from db. if it doesnt exists in db this is weird.
        # # for evnt_id, scr_evnt in scored_events.items():
        # #     if scr

    async def _fetch_upcoming_events(self):
        upcoming_events = {}
        sport_ids = []
        for sport_dict in self.active_sports:
            for sport_id, details in sport_dict.items():  # Now getting sport_id and details
                sport_ids.append(sport_id)
        try:
            tasks = [self._certain_sport_loading_upcoming_events(sport_id=sport_id) for sport_id in
                     sport_ids]
            results = await asyncio.gather(*tasks)
        except Exception as ex:
            print(ex)

        for sport_dict, result in zip(self.active_sports, results):
            result = [x for x in result if x is not None]
            for sport_id, details in sport_dict.items():  # Now getting sport_id and details
                upcoming_events[sport_id] = await self._generate_key_value_pair_for_event(result)
        self._upcoming_events = upcoming_events
        # pprint(f"upcoming_events: {upcoming_events}")
        print("Complete _fetch_upcoming_events")

    async def _generate_key_value_pair_for_event(self, events):
        updated_events_with_updated_participants = {}
        participants_manager_keys = self.participants_manager.keys()
        for event in events:
            if event.event_id in participants_manager_keys:
                event.set_participants(self.participants_manager[event.event_id].copy(), override=True)
            updated_events_with_updated_participants[event.event_id] = event
        return updated_events_with_updated_participants

    async def _cache_market_keys(self, sport_id, event: Event):
        market_keys_result = await self._sport_book_api.get_odds(sport_id, event.event_id)
        if market_keys_result['code'] != 200:
            return []
        market_keys = market_keys_result['data']
        if not market_keys:  # in case like odds api that event pulling include odds
            return
        event_market_keys = []
        for market_key in market_keys:
            if market_key["odds"]:
                odds = []
                for odd in market_key["odds"]:
                    odds.append(Odd(odd["odd_id"], odd["odd_name"], odd["rate"]))
                event_market_keys.append(MarketKey(market_key["market_key_name"], odds))
        return event_market_keys

    async def _get_order_book_of_event(self, sport_id, event: Event):
        upcoming_events_odds_refresh_time = self._prj_config["UpcomingEventOddsRefreshTimeInSeconds"]
        inplay_events_odds_refresh_time = self._prj_config["InplayEventOddsRefreshTimeInSeconds"]
        curr_time = time.time()
        if event.get_time_status() == TimeStatus.NOT_STARTED and curr_time - event.get_last_order_book_refresh_time() <= upcoming_events_odds_refresh_time and event.get_order_book() is not None:
            return event.get_order_book()

        elif event.get_time_status() == TimeStatus.IN_PLAY and curr_time - event.get_last_order_book_refresh_time() <= inplay_events_odds_refresh_time and event.get_order_book() is not None:
            return event.get_order_book()

        return await self._cache_market_keys(sport_id=sport_id, event=event)

    async def _fetch_inplay_events(self):
        inplay_events = {}
        sport_ids = []
        for sport_dict in self.active_sports:
            for sport_id, details in sport_dict.items():  # Now getting sport_id and details
                sport_ids.append(sport_id)
        tasks = [self._certain_sport_loading_inplay_events(sport_id=sport_id) for sport_id in
                 sport_ids]
        results = await asyncio.gather(*tasks)
        for sport_dict, result in zip(self.active_sports, results):
            result = [x for x in result if x is not None]
            for sport_id, details in sport_dict.items():  # Now getting sport_id and details
                inplay_events[sport_id] = await self._generate_key_value_pair_for_event(result)
        self._inplay_events = inplay_events
        # print(f"inplay_event={inplay_events}")
        print("Complete _fetch_inplay_events")

    async def get_event(self, sport_id, event_id):
        upcoming_event_refresh_interval = self._prj_config["UpcomingEventRefreshTimeInSeconds"]
        inplay_event_refresh_interval = self._prj_config["InplayEventRefreshTimeInSeconds"]
        curr_time = time.time()
        if event_id in self._upcoming_events[sport_id].keys() and curr_time - self._upcoming_events[sport_id][
            event_id].get_last_event_refresh_time() <= upcoming_event_refresh_interval:  # Event found in upcoming events
            return {
                "status": "success",
                "code": Error.SUCCESS.value,
                "data": self._upcoming_events[sport_id][event_id].to_dict()
            }
        elif event_id in self._inplay_events[sport_id].keys() and curr_time - self._inplay_events[sport_id][
            event_id].get_last_event_refresh_time() <= inplay_event_refresh_interval:  # in case that found in inplay events
            return {
                "status": "success",
                "code": Error.SUCCESS.value,
                "data": self._inplay_events[sport_id][event_id].to_dict()
            }
        else:
            event = await self._cache_event(sport_id=sport_id, event_id=event_id)
            if event is None:
                return {"status": "error", "code": Error.ERR_FAILED_TO_GET_VIEW_EVENT.value,
                        "message": "Failed to get view event"}
            # return event
            return {
                "status": "success",
                "code": Error.SUCCESS.value,
                "data": event
            }

    async def _cache_event(self, sport_id, event_id):
        try:
            response = await self._sport_book_api.get_event_by_event_id(sport_id=sport_id, event_id=event_id)
            if response['code'] != 200:
                self._logger.error(f"Failed to get from _cache_event, sport_id: {sport_id}, event_id: {event_id}")
                return
            not_parsed_event = response["data"][0]
            event = await self._parse_event(event=not_parsed_event, sport_id=sport_id)
            event.set_last_event_refresh_time(time.time())
            event_time_status = event.get_time_status()
            if event_time_status == TimeStatus.NOT_STARTED:
                self._upcoming_events[sport_id][event_id] = event
            elif event_time_status == TimeStatus.IN_PLAY:
                self._inplay_events[sport_id][event_id] = event
            else:  # Different type of event (not inplay and not upcoming )
                pass
            return event.to_dict()

        except Exception as ex:
            self._logger.error(
                f"Error while _cache_event sport_id: {sport_id}, event_id: {event_id}, ex: {ex}")
            return None

    async def get_leagues(self, sport_id):
        leagues = []
        temp_dict = {}
        if self._upcoming_events is None or self._inplay_events is None:
            return []
        for event in self._upcoming_events[sport_id].values():
            if str(event.sport.sport_id) == str(sport_id):
                leagues.append(event.league.to_dict())

        for event in self._inplay_events[sport_id].values():
            if event.sport.sport_id == sport_id:
                leagues.append(event.league.to_dict())

        for league in leagues:
            temp_dict[league['league_id']] = league
        return list(temp_dict.values())

    async def get_upcoming_events(self, sport_id=None, league_id=None):
        try:
            if sport_id and not league_id:
                events = self._upcoming_events[sport_id]

            elif league_id and sport_id:
                events = await self._extract_events_by_league_id(events=self._upcoming_events[sport_id],
                                                                 league_id=league_id)
            else:
                events = {}
                for sport_evs in self._upcoming_events.values():
                    if sport_evs:
                        for key, ev in sport_evs.items():
                            events[key] = ev
            return [event.to_dict() for event in events.values()]
        except KeyError as ex:
            print(ex)
            self._logger.error(f"Failed to return upcoming events, Exception {ex}, sport name: {sport_id}")
        except Exception as ex1:
            print(ex1)
            self._logger.error(f"Failed to return upcoming events, Exception {ex1}, sport name: {sport_id}")

    async def _extract_events_by_league_id(self, events, league_id):
        events_for_certain_league_id = {}
        for event_id, event_data in events.items():
            if str(event_data.league.league_id) == str(league_id):
                events_for_certain_league_id[event_id] = event_data
        return events_for_certain_league_id

    async def get_inplay_events(self, sport_id=None, league_id=None):
        try:
            if sport_id and not league_id:
                events = self._inplay_events[sport_id]
            elif league_id and sport_id:
                events = await self._extract_events_by_league_id(events=self._inplay_events[sport_id],
                                                                 league_id=league_id)
            else:
                events = {}
                for sport_evs in self._inplay_events.values():
                    for key, ev in sport_evs.items():
                        events[key] = ev
            return [event.to_dict() for event in events.values()]
        except KeyError as ex:
            self._logger.error(f"Failed to return inplay events, Exception {ex}, sport name: {sport_id}")
        except Exception as ex1:
            self._logger.error(f"Failed to return inplay events, Exception {ex1}, sport name: {sport_id}")

    async def enroll_participant(self, participant_data, event_id, sport_id):
        # response = await self._sport_book_api.get_event_by_event_id(sport_id=sport_id, event_id=event_id)
        # if response['code'] != 200:
        #     self._logger.error(f"Failed to get from _cache_event, sport_id: {sport_id}, event_id: {event_id}")
        #     return
        self._logger.info(
            f"Register new participant: event_id: {event_id} | sport_id: {sport_id} | participant_data: {participant_data}")
        user_id = participant_data["user_id"]
        market_key_id = participant_data["market_key_id"]
        odd_data = participant_data["odd"]
        odd_id = odd_data["odd_id"]
        odd_name = odd_data["odd_name"]
        odd_rate = odd_data["rate"]  # TODO FETCH THE ODDS AGAIN!
        odd = Odd(odd_id=odd_id, odd_name=odd_name, rate=odd_rate)
        amount = float(participant_data["amount"])
        wallet_type = await get_wallet_type(participant_data["wallet_type"])
        participant = Participant(user_id=user_id, market_key_id=market_key_id, odd=odd, amount=amount,
                                  wallet_type=wallet_type)
        participant = await self.update_odd_to_participant(event_id=event_id, participant=participant,
                                                           sport_id=sport_id)

        participants_manager_keys = self.participants_manager.keys()
        participants = None
        if self._upcoming_events is None or self._inplay_events is None:
            return False
        if event_id in self._upcoming_events[sport_id]:
            self._upcoming_events[sport_id][event_id].set_participants(participant)
            self.events_with_participants[event_id] = self._upcoming_events[sport_id][event_id]
        elif event_id in self._inplay_events[sport_id]:
            self._inplay_events[sport_id][event_id].set_participants(participant)
            self.events_with_participants[event_id] = self._inplay_events[sport_id][event_id]
        if event_id in participants_manager_keys:
            self.participants_manager[event_id].append(participant)
            participants = [participant_dict.to_dict() for participant_dict in self.participants_manager[event_id]]
        else:
            self.participants_manager[event_id] = [participant]
            participants = [participant.to_dict()]

        try:
            response = await self.pool.send_payment_to_pool(user_id, wallet_type, amount, "Place Bet")

            res = await self.db.post(
                {"path": f"ParticipantsManager/{event_id}",
                 "data": {"Participants": participants, "CompletedWithPrizes": False}})
            try:
                if event_id in self.saved_events:
                    return True
                await self.save_event_on_db(event_id, sport_id)
                self.saved_events.append(event_id)
                self._logger.info(f"Success to backup in db the event: {event_id}")

            except Exception as ex:
                self._logger.critical(f"Failed to backup in db the event: {event_id}, ex: {ex}")
                return False

        except Exception as ex:
            self._logger.critical(f"Failed to backup in db the participants: {participants}, ex: {ex}")
            return False

        return True

    async def get_odd(self, event_id, sport_id, market_key_name, odd_id):
        try:
            event = (await self.get_event(sport_id, event_id))['data']
            order_book = event['order_book']
            for book in order_book:
                if book['market_key_name'] == market_key_name:
                    for odd in book['odds']:
                        if odd['odd_id'] == odd_id:
                            return odd
            return None
        except Exception as ex:
            self._logger.error(
                f"Bug from get_odd, event_id: {event_id}, sport_id: {sport_id}, market_key_name: {market_key_name}, odd_id: {odd_id}, ex: {ex}")
        return None

    async def get_pool(self):
        pool = await self.pool.to_dict()
        return {
            "status": "success",
            "code": Error.SUCCESS.value,
            "data": pool
        }

    async def get_league_by_event_id(self, event_id):
        for sport in list(self._upcoming_events.keys()):
            if event_id in list(self._upcoming_events[sport].keys()):
                return self._upcoming_events[sport][event_id].league.league_id
        for sport in list(self._inplay_events.keys()):
            if event_id in list(self._inplay_events[sport].keys()):
                return self._inplay_events[sport][event_id].league.league_id
        self._logger.error(
            f"event_id {event_id} not found in self._upcoming_events or in self._inplay_events. probably can't enroll participant")
        return None

    async def update_odd_to_participant(self, sport_id, event_id, participant):
        sport_league_id = await self.get_league_by_event_id(event_id=event_id)

        res = await self._sport_book_api.get_event_odds(sport_id=sport_id, event_id=event_id,
                                                        sport_league_id=sport_league_id)
        if not res:
            self._logger.error(f"Failed to update rate for event_id: {event_id}, no bet setted")
            return None
        for market_key in res.keys():
            if market_key == participant.market_key_id:
                odds = res[market_key]
                for odd in odds:
                    if odd.odd_id == participant.odd.odd_id:
                        participant.odd.rate = odd.rate
                        return participant
                self._logger.error(f"Failed to update rate for event_id: {event_id}, no bet setted")
                return None
        return None

    async def save_event_on_db(self, event_id, sport_id):
        event_response = await self.get_event(sport_id, event_id)
        if event_response['code'] == Error.SUCCESS.value:
            res = await self.db.post(
                {"path": f"Events/{event_id}",
                 "data": {"sport_id": sport_id, "data": event_response['data']}})
            if not res:
                self._logger.error(f"Failed to back-up event: Sport ID: {sport_id} | Event ID:{event_id}")
                return False
            return True
        else:
            self._logger.error(f"Failed to back-up event: Sport ID: {sport_id} | Event ID:{event_id}")
            return False

    async def get_user_bets(self, user_id):
        live_participants_event_ids = {}
        history_participants_event_ids = {}

        for event_id, participants_list in self.participants_manager.items():
            for participant in participants_list:
                if participant.user_id == user_id:
                    tp = participant.to_dict()
                    tp['wallet_type'] = WalletTypes(tp['wallet_type']).name
                    live_participants_event_ids[event_id] = tp

        for event_id, participants_list in self.history_participants.items():
            for participant in participants_list:
                if participant.user_id == user_id:
                    tp = participant.to_dict()
                    tp['wallet_type'] = WalletTypes(tp['wallet_type']).name
                    history_participants_event_ids[event_id] = tp
        return {
            "status": "success",
            "code": Error.SUCCESS.value,
            "data": {"live_bets": live_participants_event_ids, "history_bets": history_participants_event_ids}
        }


mock = {'amount': 250.0,
        'bet_time': 1705587926.5556452,
        'market_key_id': 'h2h',
        'odd': {'odd_id': 'Drexel Dragons',
                'odd_name': 'Drexel Dragons',
                'rate': 1.2,
                'update_time': 1705587904.8478725},
        'user_id': '5200784418',
        'wallet_type': 'DEMO'}

# import asyncio
# import websockets
#
# class WSServer:
#     def __init__(self):
#         self.target_client = None
#         self.clients = set()
#
#     async def handle_client(self, websocket, path):
#         self.clients.add(websocket)
#         try:
#             if not self.target_client:
#                 self.target_client = websocket
#                 await self.target_client.send("You are the target client. Ready to receive messages.")
#
#             # Keep the connection open by awaiting a future that never completes
#             await asyncio.Future()
#
#         except websockets.exceptions.ConnectionClosedOK:
#             pass  # Handle closed connections gracefully
#         finally:
#             if self.target_client == websocket:
#                 self.target_client = None
#
#     async def send_message(self, message):
#         if self.target_client and self.target_client in self.clients:
#             try:
#                 await self.target_client.send(message)
#             except websockets.exceptions.ConnectionClosedOK:
#                 pass  # Handle closed connections gracefully
#
#     async def run_server(self):
#         server = await websockets.serve(self.handle_client, "localhost", 1010)


# async def main():
#     server = WebSocketServer()
#     server_task = asyncio.get_event_loop().create_task(server.run_server())
#
#     runner = Runner(server)
#     await asyncio.gather(runner._init(), server_task)
#     # asyncio.run(await runner._init())
#     # asyncio.get_event_loop().run_until_complete(server_task)
#
#
# print(1)
# asyncio.run(main())
