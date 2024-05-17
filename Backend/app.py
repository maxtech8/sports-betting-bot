import asyncio
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint

from flask import Flask, jsonify, request

# Import your classes (ensure these are implemented correctly)
from Gaming.Runner import Runner
from Users.UserFactory import UserFactory

# from WebSocketServer import WebSocketServer

app = Flask(__name__)
# server = WebSocketServer()
# server_task = asyncio.get_event_loop().create_task(server.run_server())

runner = Runner()

# Global thread pool executor
executor = ThreadPoolExecutor()

# In-memory "database" for demonstration purposes
users = {}


# Initialize runner asynchronously
async def load_runner():
    await runner._init()


# Run the load_runner function in the background when the app starts
def start_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(load_runner())
    loop.close()


executor.submit(start_async_loop)


@app.route('/api/v1/getUser/<user_id>', methods=['GET'])
def get_user(user_id):
    user = users.get(user_id)

    if user:
        future = executor.submit(asyncio.run, user.to_dict())
        user_dict = future.result()
        return jsonify(user=user_dict), 200
    else:
        return jsonify(error="User not found"), 404


@app.route('/api/v1/createUser', methods=['POST'])
def create_user():
    data = request.json
    user_id = str(data.get('user_id'))

    if user_id is None or user_id in users:
        return jsonify(error="Invalid or existing user_id"), 400

    future = executor.submit(asyncio.run, UserFactory.create_user(user_id))
    new_user = future.result()

    future = executor.submit(asyncio.run, new_user.to_dict())
    new_user_to_dict = future.result()

    users[user_id] = new_user

    return jsonify(id=user_id, created_user=new_user_to_dict), 201


@app.route('/api/v1/updateUser/<user_id>', methods=['PUT'])
def update_user(user_id):
    if user_id in users:
        data = request.json
        users[user_id].update(data)
        return jsonify(id=user_id, updated_user=data)
    else:
        return jsonify(error="User not found"), 404


@app.route('/api/v1/deleteUser/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    user_id = str(user_id)
    if user_id in users:
        del users[user_id]
        return jsonify(message="User deleted successfully")
    else:
        return jsonify(error="User not found"), 404


@app.route('/api/v1/approveTermsAndConditions', methods=['POST'])
def approve_terms_and_conditions():
    data = request.json
    user_id = str(data.get('user_id'))

    if user_id is None or user_id not in users:
        return jsonify(error="Invalid user_id"), 400

    executor.submit(asyncio.run, users[user_id].set_terms_and_conditions_approved(True))
    return jsonify(id=user_id, created_user=data), 201


@app.route('/api/v1/getUpcomingEvents/<sport_id>', methods=['GET'])
def get_upc_events(sport_id):
    future = executor.submit(asyncio.run, runner.get_upcoming_events(sport_id))
    events = future.result()

    if events:
        return jsonify(upcoming_events=events), 200
    else:
        return jsonify(error="No events found for given sport"), 404


@app.route('/api/v1/getLeagues/<sport_id>', methods=['GET'])
def get_leagues(sport_id):
    future = executor.submit(asyncio.run, runner.get_leagues(str(sport_id)))
    leagues = future.result()
    if leagues:
        return jsonify(leagues=leagues), 200
    else:
        return jsonify(error="No events found for given sport"), 404


@app.route('/api/v1/getEvent/<sport_id>/<event_id>', methods=['GET'])
def get_event(sport_id, event_id):
    future = executor.submit(asyncio.run, runner.get_event(sport_id, event_id))
    event = future.result()
    if event is not None:
        return jsonify(event=event), 200
    else:
        return jsonify(error="No events found for given sport"), 404


@app.route('/api/v1/getEvents/<sport_id>/<league_id>', methods=['GET'])
def get_events(sport_id, league_id):
    future = executor.submit(asyncio.run, runner.get_upcoming_events(sport_id, league_id))
    upcoming_e = future.result()
    future = executor.submit(asyncio.run, runner.get_inplay_events(sport_id, league_id))
    inplay_e = future.result()
    if upcoming_e is not None and inplay_e is not None:
        return jsonify(upcoming_events=upcoming_e, inplay_events=inplay_e), 200
    else:
        return jsonify(error="No events found for given sport"), 404


@app.route('/api/v1/getAllEvents', methods=['GET'])
def get_all_events():
    future = executor.submit(asyncio.run, runner.get_upcoming_events())
    upcoming_e = future.result()
    future = executor.submit(asyncio.run, runner.get_inplay_events())
    inplay_e = future.result()
    if upcoming_e is not None and inplay_e is not None:
        return jsonify(upcoming_events=upcoming_e, inplay_events=inplay_e), 200
    else:
        return jsonify(error="No events found for given sport"), 404


@app.route('/api/v1/getSports', methods=['GET'])
def get_sports():
    future = executor.submit(asyncio.run, runner.get_played_sports())
    sports = future.result()

    if sports:
        return jsonify(sports=sports), 200
    else:
        return jsonify(error="No sports found"), 404


@app.route('/api/v1/getOdd/<event_id>/<sport_id>/<market_key_name>/<odd_id>', methods=['GET'])
def get_odd(event_id, sport_id, market_key_name, odd_id):
    future = executor.submit(asyncio.run, runner.get_odd(event_id, sport_id, market_key_name, odd_id))
    odd = future.result()

    if odd:
        return jsonify(odd=odd), 200
    else:
        return jsonify(error="No sports found"), 404


@app.route('/api/v1/placeBet', methods=['POST'])
def request_place_bet():
    # Ensure JSON payload is present
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    data = request.get_json()
    participant = data.get('participant')
    event_id = data.get('event_id')
    sport_id = data.get('sport_id')

    # Handle the logic here, adjust according to your application's logic
    future = executor.submit(asyncio.run, runner.enroll_participant(participant, event_id, sport_id))
    result = future.result()

    if not result:
        return jsonify(error="Invalid request"), 400
    return jsonify(response="success"), 201


@app.route('/api/v1/withdrawalExternalAddress/<confirmation_id>', methods=['POST'])
def request_withdrawal_external_address(confirmation_id):
    try:
        print(f"confirmation_id = {confirmation_id}")
        # Ensure JSON payload is present
        if not request.is_json:
            return jsonify({"error": "Missing JSON in request"}), 400

        data = request.get_json()

        # Handle the logic here, adjust according to your application's logic
        future = executor.submit(asyncio.run,
                                runner.wallet_manager.withdraw_request(data['user_id'], data['amount'], data['address'],
                                                                        data['wallet_type']))
        result = future.result()
        if not result or result['status'] == 'error':
            return jsonify(error=result['data']), 400
        return jsonify(response=result['data']), 201
    except Exception as ex:
        print(f"request_withdrawal_external_address error {ex}")
    


@app.route('/api/v1/getMyBets/<user_id>', methods=['GET'])
def request_get_my_bets(user_id):
    # Ensure JSON payload is present
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    # Handle the logic here, adjust according to your application's logic
    future = executor.submit(asyncio.run,
                             runner.get_user_bets(user_id))
    result = future.result()
    if not result or result['status'] == 'error':
        return jsonify(error=result['data']), 400
    return jsonify(response=result['data']), 200

@app.route('/api/v1/getPool', methods=['GET'])
def request_get_pool():
    # Ensure JSON payload is present
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    # Handle the logic here, adjust according to your application's logic
    future = executor.submit(asyncio.run,
                             runner.get_pool())
    result = future.result()
    print(result)
    if not result or result['status'] == 'error':
        return jsonify(error=result['data']), 400
    return jsonify(response=result['data']), 201


if __name__ == '__main__':
    app.run(debug=False)
