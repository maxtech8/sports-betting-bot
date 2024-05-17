from pprint import pprint

import requests


class TheOddsAPI:
    def __init__(self):
        self.api_key = "04ba75812b679b3cf596b2b7a71c4c31"
        self.base_url = 'https://api.the-odds-api.com/v4'

    def _get_sports_odds_api(self):
        response = requests.get(f'{self.base_url}/sports', params={'apiKey': self.api_key})
        if response.status_code == 200:
            return response.json()
        return False

    def _get_odds_odds_api(self, sport):
        response = requests.get(f'{self.base_url}/sports/{sport}/odds',
                                params={'apiKey': self.api_key, 'regions': 'us', 'dateFormat': 'unix'})
        if response.status_code == 200:
            return response.json()
        return False

api = TheOddsAPI()
pprint(api.get_sports())
