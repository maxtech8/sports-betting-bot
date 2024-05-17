from abc import ABC, abstractmethod

from Databases.Remote.RemoteStorage import RemoteStorage
from Logger.CustomLogger import CustomLogger
from Wallets.WalletsManagerSingleton import WalletsManagerSingleton
from Configurations import ConfigSingleton

logger = CustomLogger.get_instance()
db = RemoteStorage.get_storage()


class AbstractWallet(ABC):
    def __init__(self, user_id):
        self.user_id = user_id
        self._balance = None
        self.wallet_category = None
        self.wallet_manager = WalletsManagerSingleton.get_instance()
        self._prj_config = ConfigSingleton.ConfigSingleton.get_instance().get_prjConfig()

    @abstractmethod
    async def init_wallet(self, user_id):
        """
        Initiate wallet for new Wallet class instance
        """
        pass

    @abstractmethod
    async def get_wallet_type(self):
        """
        :return: Type of the wallet e.g. Demo, BNB
        """
        pass

    @abstractmethod
    async def to_dict(self):
        """
        :return: dictionary of the wallet
        """
        pass

    async def get_balance(self):
        return self._balance

    async def send_transaction(self, wallet: 'AbstractWallet', amount: float, description=None):
        try:
            print(f"send_transaction")
            if amount > self._balance:
                logger.info(
                    f"Attempt send transaction: User ID: {self.user_id} | Recipient: {wallet.user_id} | Amount: {amount} | New Balance: {await self.get_balance()} | Description: Failed Insufficient funds")
                return False

            self._balance -= amount
            await self.save_balance_on_db()
            logger.info(
                f"Send transaction: User ID: {self.user_id} | Recipient: {wallet.user_id} | Amount: {amount} | New Balance: {await self.get_balance()} | Description: {description}")
            print(self._prj_config["Commission"]["OwnerID"])
            print(await wallet.get_wallet_type())
            commssion_wallet = await self.wallet_manager.get_wallet(self._prj_config["Commission"]["OwnerID"],
                                                                    wallet_type=await wallet.get_wallet_type())
            print(f"commssion_wallet = {commssion_wallet}")
            percentage = self._prj_config["Commission"]["Percentage"] / 100
            await commssion_wallet.receive_transaction(amount * percentage)
            return await wallet.receive_transaction(amount * (1 - percentage))
        except Exception as ex:
            print(f"send_transaction error: {ex}")
        

    async def receive_transaction(self, amount: float, description=None):
        try:
            print(f"receive_transaction")
            self._balance += amount
            await self.save_balance_on_db()
            logger.info(
                f"Receive transaction: User ID: {self.user_id} | Amount: {amount} | New Balance: {await self.get_balance()} | Description: {description}")
            return True
        except Exception as ex:
            print(f"receive_transaction error: {ex}")
            return False

    async def save_balance_on_db(self):
        try:
            await db.update(
                {"path": f"Wallets/{self.user_id}/{self.wallet_category.value}/{(await self.get_wallet_type()).name}",
                "data": {"balance": self._balance}})
            logger.info(
                f"Save Balance On DB: User ID: {self.user_id} | Balance: {self._balance}")
        except Exception as ex:
            print(f"save_balance_on_db error: {ex}")
