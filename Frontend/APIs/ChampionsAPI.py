import json
from pprint import pprint

import requests


class ChampionsAPI:
    def __init__(self):
        self.BASE_URL = "http://127.0.0.1:5000/api/v1"

    async def get_user(self, user_id):
        """GET request to retrieve a user."""
        response = requests.get(f"{self.BASE_URL}/getUser/{user_id}")
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"Failed to retrieve user, status_code: ", response.status_code)
        else:
            print(f"Failed to retrieve user, status_code: ", response.status_code)

        return False

    async def create_user(self, user_id):
        """POST request to create a new user."""
        data = {'user_id': user_id, 'terms_and_conditions_approved': False}
        response = requests.post(f"{self.BASE_URL}/createUser", json=data)
        if response.status_code == 201:
            return True
        else:
            print("Failed to create user", response.status_code)
            return False

    async def update_user(self, user_id, new_data):
        """PUT request to update an existing user."""
        response = requests.put(f"{self.BASE_URL}/updateUser/{user_id}", json=new_data)
        if response.status_code == 200:
            return True
        else:
            print("Failed to update user", response.status_code)
            return False

    async def delete_user(self, user_id):
        """DELETE request to delete a user."""
        response = requests.delete(f"{self.BASE_URL}/deleteUser/{user_id}")
        if response.status_code == 200:
            return True
        else:
            print("Failed to delete user", response.status_code)
            return False

    async def approve_terms_and_conditions(self, user_id):
        """POST request to create a new user."""
        data = {'user_id': user_id}
        response = requests.post(f"{self.BASE_URL}/approveTermsAndConditions", json=data)
        if response.status_code == 201:
            return True
        else:
            print("Failed to approve terms and conditions", response.status_code)
            return False

    async def get_event(self, sport_id, event_id):
        """GET request to retrieve events."""
        # Ensure that league_id has a value, or default to an empty string
        response = requests.get(f"{self.BASE_URL}/getEvent/{sport_id}/{event_id}")
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"Failed to retrieve upcoming events, status_code: ", response.status_code)
        else:
            print(f"Failed to retrieve upcoming events, status_code: ", response.status_code)
        return False

    async def get_events(self, sport_id=None, league_id=None):
        """GET request to retrieve events."""
        # Ensure that league_id has a value, or default to an empty string
        league_id = league_id or ''
        sport_id = sport_id or ''
        response = requests.get(f"{self.BASE_URL}/getEvents/{sport_id}/{league_id}")
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"Failed to retrieve upcoming events, status_code: ", response.status_code)
        else:
            print(f"Failed to retrieve upcoming events, status_code: ", response.status_code)
        return False

    async def get_all_events(self):
        """GET request to retrieve events."""
        # Ensure that league_id has a value, or default to an empty string

        response = requests.get(f"{self.BASE_URL}/getAllEvents")
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"Failed to retrieve upcoming events, status_code: ", response.status_code)
        else:
            print(f"Failed to retrieve upcoming events, status_code: ", response.status_code)
        return False

    async def get_sports(self):
        """GET request to retrieve a user."""
        response = requests.get(f"{self.BASE_URL}/getSports")
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"Failed to retrieve sports, status_code: ", response.status_code)
        else:
            print(f"Failed to retrieve sports, status_code: ", response.status_code)
        return False

    async def get_leagues(self, sport_id):
        """GET request to retrieve a user."""
        response = requests.get(f"{self.BASE_URL}/getLeagues/{sport_id}")
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"Failed to retrieve sports, status_code: ", response.status_code)
        else:
            print(f"Failed to retrieve sports, status_code: ", response.status_code)
        return False

    async def get_odd(self, event_id, sport_id, market_key_name, odd_id):
        """GET request to retrieve a user."""
        response = requests.get(f"{self.BASE_URL}/getOdd/{event_id}/{sport_id}/{market_key_name}/{odd_id}")
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"Failed to retrieve sports, status_code: ", response.status_code)
        else:
            print(f"Failed to retrieve sports, status_code: ", response.status_code)
        return False

    async def place_bet(self, participant, event_id, sport_id):
        """POST request to place a bet."""
        data = {
            "participant": participant,
            "event_id": event_id,
            "sport_id": sport_id
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{self.BASE_URL}/placeBet", data=json.dumps(data), headers=headers)
        if response.status_code == 201:
            return response.json()
        elif response.status_code == 404:
            print(f"Failed to place bet, status_code: ", response.status_code)
        else:
            print(f"Error, status_code: ", response.status_code)
        return False

    async def withdrawal_external_address(self, withdrawal, confirmation_id):
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{self.BASE_URL}/withdrawalExternalAddress/{confirmation_id}",
                                 data=json.dumps(withdrawal), headers=headers)
        if response.status_code == 201:
            return response.json()
        elif response.status_code == 400:
            print(f"Failed to withdrawal, status_code: ", response.status_code)
        else:
            print(f"Error, status_code: ", response.status_code)
        return False

    async def get_pool(self):
        headers = {'Content-Type': 'application/json'}
        response = requests.get(f"{self.BASE_URL}/getPool", headers=headers)
        if response.status_code == 201:
            return response.json()
        elif response.status_code == 400:
            print(f"Failed to get pool, status_code: ", response.status_code)
        else:
            print(f"Error, status_code: ", response.status_code)
        return False

    async def get_my_bets(self, user_id):
        headers = {'Content-Type': 'application/json'}
        response = requests.get(f"{self.BASE_URL}/getMyBets/{user_id}", headers=headers)
        if response.status_code == 200:
            return response.json()['response']
        elif response.status_code == 400:
            print(f"Failed to get pool, status_code: ", response.status_code)
        else:
            print(f"Error, status_code: ", response.status_code)
        return False
