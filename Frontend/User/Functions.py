from APIs.APIsSingleton import APIsSingleton

APIs_singleton = APIsSingleton.get_instance()
champions_api = APIs_singleton.get_champions_api()


async def create_user(user_id):
    result = await champions_api.create_user(user_id)
    return result


async def get_user(user_id):
    result = await champions_api.get_user(user_id)
    return result
