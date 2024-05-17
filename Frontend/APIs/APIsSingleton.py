import json
from APIs.ChampionsAPI import ChampionsAPI


class APIsSingleton:
    _instance = None

    def _init_APIs(self):
        self._ChampionsAPI = ChampionsAPI()

        # Here you can open new configuration files

    @staticmethod
    def get_instance():
        if APIsSingleton._instance is None:
            APIsSingleton._instance = APIsSingleton()
            APIsSingleton._instance._init_APIs()
        return APIsSingleton._instance

    def get_champions_api(self):
        return self._ChampionsAPI
