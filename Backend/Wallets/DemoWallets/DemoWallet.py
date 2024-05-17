from Databases.Remote.RemoteStorage import RemoteStorage
from Logger.CustomLogger import CustomLogger
from Wallets.AbstractWallet import AbstractWallet
from Wallets.WalletTypes import WalletTypes, WalletCategories

logger = CustomLogger.get_instance()
db = RemoteStorage.get_storage()


class DemoWallet(AbstractWallet):

    def __init__(self, user_id):
        super().__init__(user_id)
        self.wallet_category = WalletCategories.DEMO

    async def init_wallet(self, user_id):
        logger.info(
            f"Init wallet: User ID: {self.user_id}")
        wallet = await self.import_wallet()
        if wallet is not None:

            self._balance = wallet['balance']
        else:

            await self.set_balance(1000)

            await self.export_wallet(await self.get_balance())

    async def get_wallet_type(self):
        return WalletTypes.DEMO

    async def to_dict(self):
        return {
            "wallet_type": (await self.get_wallet_type()).name,
            "wallet_category": self.wallet_category.name,
            "balance": await self.get_balance(),
        }

    async def export_wallet(self, balance):
        await db.post(
            {"path": f"Wallets/{self.user_id}/{self.wallet_category.value}/{(await self.get_wallet_type()).name}",
             "data": {"balance": balance}})
        logger.info(
            f"Export {self.wallet_category.value} Wallet: User ID: {self.user_id} | Balance: {balance}")

    async def import_wallet(self):
        wallet = await db.get(
            {"path": f"Wallets/{self.user_id}/{self.wallet_category.value}/{(await self.get_wallet_type()).name}"})

        logger.info(
            f"Import {self.wallet_category.value} Wallet: User ID: {self.user_id} | Wallet: {wallet}")
        return wallet

    async def set_balance(self, balance):
        self._balance = balance
