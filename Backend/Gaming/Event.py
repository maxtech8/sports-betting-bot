import time
from enum import Enum

from Gaming import Sport
from Gaming.League import League
from Gaming.Score import Score


class TimeStatus(Enum):
    NOT_STARTED = 0
    IN_PLAY = 1
    TO_BE_FIXED = 2
    ENDED = 3
    POSTPONED = 4
    CANCELLED = 5
    WALKOVER = 6
    INTERRUPTED = 7
    ABANDONED = 8
    RETIRED = 9
    SUSPENDED = 10
    DECIDED_BY_FA = 11
    REMOVED = 99


class Event:

    def __init__(self, teams: list, commence_time: int, sport: Sport,
                 league: League, time_status: TimeStatus, event_id, participants: list = None):
        """
        :param participants: List of Participant
        :param teams: List of Team
        :param commence_time: unix time
        :param sport: Sport class instance
        """
        self.event_id = event_id
        self.participants = participants
        self.teams = teams
        self.commence_time = commence_time
        self.sport = sport
        self.league = league
        self._time_status = time_status
        self._last_event_refresh_time = time.time()
        self._last_order_book_refresh_time = time.time()
        self._order_book = None
        self._score = None
        self.is_scores_notified_to_client = False

    def get_last_order_book_refresh_time(self):
        return self._last_order_book_refresh_time

    def notify_to_client(self):
        self.is_scores_notified_to_client = True

    def is_notified_to_client(self):
        return self.is_scores_notified_to_client

    def set_participants(self, participant, override=False):
        if override:
            self.participants = participant  # Sent as list of participants
            return
        if self.participants is None:
            self.participants = [participant]
        else:
            self.participants.append(participant)

    def set_last_order_book_refresh_time(self, time):
        self._last_order_book_refresh_time = time

    def get_last_event_refresh_time(self):
        return self._last_event_refresh_time

    def set_last_event_refresh_time(self, time):
        self._last_event_refresh_time = time

    def get_order_book(self):
        return self._order_book

    def set_order_book(self, order_book: list):
        self._order_book = order_book

    def get_score(self):
        return self._score

    def set_score(self, score):
        self._score = score

    def get_time_status(self):
        return self._time_status

    def set_time_status(self, time_status: TimeStatus):
        self._time_status = time_status

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "participants": [participant.to_dict() for participant in
                             self.participants] if self.participants is not None else [],
            "teams": [team.to_dict() for team in self.teams],
            "commence_time": self.commence_time,
            "sport": self.sport.to_dict() if self.sport else None,
            "league": self.league.to_dict() if self.league else None,
            "time_status": self._time_status.value if self._time_status else None,
            "order_book": [] if self._order_book is None else [market_key.to_dict() for market_key in
                                                               self._order_book],
            "score": [] if self._score is None else self._score.to_dict()
        }
