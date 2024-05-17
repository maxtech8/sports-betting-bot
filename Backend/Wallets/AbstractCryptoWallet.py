from abc import ABC, abstractmethod

from APIs.Errors import Error
from Databases.Remote.RemoteStorage import RemoteStorage
from Logger.CustomLogger import CustomLogger
from Wallets.AbstractWallet import AbstractWallet
from Wallets.WalletTypes import WalletCategories

db = RemoteStorage.get_storage()
logger = CustomLogger.get_instance()


class AbstractCryptoWallet(AbstractWallet, ABC):
    def __init__(self, asset, blockchain, user_id):
        super().__init__(user_id)
        self.asset = asset
        self.blockchain = blockchain
        self._private_key = None
        self._address = None
        self.wallet_category = WalletCategories.CRYPTO

    @abstractmethod
    async def generate_address(self):
        """
        Generate a new wallet address.
        """
        pass

    @abstractmethod
    async def sign_transaction(self, to_addr, amount: float):
        """
        Sign a transaction with the wallet's private key.
        """
        pass

    @abstractmethod
    async def verify_transaction(self, tx_hash):
        """
        Verify a transaction.
        """
        pass

    @abstractmethod
    async def get_crypto_balance(self):
        """
        Get the crypto balance on blockchain
        """
        pass

    @abstractmethod
    async def create_crypto_wallet(self):
        """
        Create new crypto wallet
        """
        pass

    async def to_dict(self):
        return {
            "wallet_type": (await self.get_wallet_type()).name,
            "wallet_category": self.wallet_category.name,
            "balance": await self.get_balance(),
            "deposit_key": self._address,
        }

    async def init_wallet(self, user_id):
        logger.info(
            f"Init wallet: User ID: {self.user_id}")
        wallet = await self.import_wallet()
        if wallet is not None:

            self._address = wallet['address']
            self._private_key = await self.decrypt_private_key(wallet['private_key'])
            self._balance = wallet['balance']
        else:
            address, private_key = await self.create_crypto_wallet()

            await self.set_private_key(private_key)
            await self.set_address(address)
            await self.set_balance(0)

            await self.export_wallet(await self.get_balance(), address, private_key)

    async def export_wallet(self, balance, address, private_key):
        await db.post(
            {"path": f"Wallets/{self.user_id}/{self.wallet_category.value}/{(await self.get_wallet_type()).name}",
             "data": {"address": address,
                      "private_key": await self.encrypt_private_key(private_key),
                      "balance": balance}})
        logger.info(
            f"Export Crypto Wallet: User ID: {self.user_id} | Address: {address} | Balance: {balance} | Private Key: {await self.encrypt_private_key(private_key)}")

    async def import_wallet(self):
        wallet = await db.get(
            {"path": f"Wallets/{self.user_id}/{self.wallet_category.value}/{(await self.get_wallet_type()).name}"})

        logger.info(
            f"Import Crypto Wallet: User ID: {self.user_id} | Wallet: {wallet}")
        return wallet

    async def get_address(self):
        return self._address

    async def set_address(self, address):
        self._address = address

    async def set_private_key(self, private_key):
        self._private_key = private_key

    async def set_balance(self, balance):
        self._balance = balance

    async def encrypt_private_key(self, private_key):
        return private_key

    async def decrypt_private_key(self, private_key):
        return private_key
