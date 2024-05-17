from abc import ABC, abstractmethod
from Configurations import ConfigSingleton
from Logger.CustomLogger import CustomLogger


class Database(ABC):
    _instance = None

    def __init__(self):
        self.logger = CustomLogger.get_instance()
        self.config = ConfigSingleton.ConfigSingleton.get_instance()
        self.prjConfig = self.config.get_prjConfig()

    @classmethod
    def get_instance(cls):
        if Database._instance is None:
            Database._instance = cls()
        return Database._instance

    @abstractmethod
    def init_db(self, *args):
        pass

    @abstractmethod
    def close_db(self, *args):
        pass

    @abstractmethod
    def update(self, *args):
        pass

    @abstractmethod
    def post(self, *args):
        pass

    @abstractmethod
    def get(self, *args):
        pass

    @abstractmethod
    def delete(self, *args):
        pass
