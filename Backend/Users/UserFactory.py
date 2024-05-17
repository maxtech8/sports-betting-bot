import asyncio
import time

from Configurations import ConfigSingleton
from Users.User import User
from Wallets.WalletTypes import WalletTypes
from Wallets.WalletsFactory import WalletsFactory


class UserFactory:
    is_init = False

    @staticmethod
    async def _init_users():
        if not UserFactory.is_init:
            _prj_config = ConfigSingleton.ConfigSingleton.get_instance().get_prjConfig()
            UserFactory.is_init = True
            owner_id = _prj_config["Commission"]["OwnerID"]
            user = User(user_id=owner_id)
            tasks = [WalletsFactory.create_wallet(type_, owner_id) for type_ in WalletTypes]
            user_wallets = await asyncio.gather(*tasks)
            await user.set_wallets(user_wallets)


    @staticmethod
    async def create_user(user_id: str):
        await UserFactory._init_users()

        # Initialize the user
        user = User(user_id)
        start = time.time()
        tasks = [WalletsFactory.create_wallet(type_, user_id) for type_ in WalletTypes]
        user_wallets = await asyncio.gather(*tasks)
        await user.set_wallets(user_wallets)

        print("Load wallets " + str(time.time() - start))

        return user
