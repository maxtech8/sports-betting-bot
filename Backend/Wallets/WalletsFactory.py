from Wallets.Crypto.BNBWallet import BNBWallet
from Wallets.Crypto.ETHWallet import ETHWallet
from Wallets.Crypto.SOLWallet import SOLWallet
from Wallets.DemoWallets.DemoWallet import DemoWallet
from Wallets.WalletTypes import WalletTypes
from Wallets.WalletsManagerSingleton import WalletsManagerSingleton

wallet_manager = WalletsManagerSingleton.get_instance()


class WalletsFactory:
    @staticmethod
    async def _init_master_wallets():
        for wallet_type in WalletTypes:
            await WalletsFactory.create_wallet(wallet_type, "master")

    @staticmethod
    async def get_wallet(user_id, wallet_type):
        # this method return the wallet / None if not found
        wallets = await wallet_manager.get_wallets()
        for wallet in wallets:
            curr_wallet_type = await wallet.get_wallet_type()
            if wallet.user_id == user_id and curr_wallet_type.value == wallet_type.value:
                return wallet
        return None

    @staticmethod
    async def create_wallet(wallet_type: WalletTypes, user_id: str):
        user_wallet = await WalletsFactory.get_wallet(user_id, wallet_type)
        if user_wallet:
            return user_wallet
        wallet = None
        if len(wallet_manager.master_wallets) == 0 and user_id != "master":
            await WalletsFactory._init_master_wallets()

        if wallet_type.value == 1:
            wallet = DemoWallet(user_id)


        elif wallet_type.value == 801:
            wallet = ETHWallet(user_id)

        elif wallet_type.value == 802:
            wallet = BNBWallet(user_id)

        elif wallet_type.value == 803:
            wallet = SOLWallet(user_id)
            
        await wallet.init_wallet(user_id)
        if 'master' in user_id:
            wallet_manager.master_wallets[wallet_type.name] = wallet
        else:
            await wallet_manager.add_wallet(wallet)
        # print(user_id)
        # print(await wallet.to_dict())
        return wallet
