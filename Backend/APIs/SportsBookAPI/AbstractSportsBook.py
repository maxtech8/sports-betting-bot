from abc import ABC, abstractmethod
from Logger.CustomLogger import CustomLogger

from Configurations import ConfigSingleton


class AbstractSportsBook(ABC):
    def __init__(self):
        self.logger = CustomLogger.get_instance()
        self.sports_config = ConfigSingleton.ConfigSingleton.get_instance().get_sport_config()
        self.prj_config = ConfigSingleton.ConfigSingleton.get_instance().get_prjConfig()

    @abstractmethod
    async def get_upcoming_events(self, sport_name, day):
        pass

    @abstractmethod
    async def get_ended_events(self, sport_name, day):
        pass

    @abstractmethod
    async def get_inplay_events(self, sport_id):
        pass

    @abstractmethod
    async def get_event_by_event_id(self, event_id):
        pass
