import asyncio
import time

from APIs.Errors import Error
from Databases.Local.LocalStorage import LocalStorage
from Databases.Remote.RemoteStorage import RemoteStorage
from Logger.CustomLogger import CustomLogger
from Wallets.WalletTypes import WalletTypes, get_wallet_type

local_storage = LocalStorage.get_instance()
logger = CustomLogger.get_instance()
db = RemoteStorage.get_storage()


class WalletsManagerSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            logger.info("Creating a new instance of WalletsManagerSingleton")
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if WalletsManagerSingleton._instance is not None:
            logger.critical("Attempt to create two instances of WalletsManagerSingleton")
            raise Exception("Creating two instances of the same singleton WalletsManagerSingleton")
        logger.info("Initializing WalletsManagerSingleton")
        self._wallets = []
        self.master_wallets = {}


    async def init_pending_transactions(self):
        try:
            if await local_storage.get_resource("pending_transaction") is None:
                print(f"Initializing pending transactions in local storage")
                logger.info("Initializing pending transactions in local storage")
                await local_storage.post_resource("pending_transaction", {type_.name: [] for type_ in WalletTypes})
        except Exception as ex:
            print(f"init_pending_transactions error: {ex}")
        
    async def add_wallet(self, wallet):

        #   async with self.wallet_sem:
        logger.info(f"Adding new wallet: {wallet}")
        self._wallets.append(wallet)

    async def transactions_monitor(self):
        logger.info("Starting transaction monitor")
        print(f"Starting transaction monitor...")
        while True:
            try:
                await self.init_pending_transactions()
                await self.process_wallet_transactions()
                await self.verify_and_process_transactions()
            except Exception as ex:
                print(f"Exception from transactions_monitor: {ex}")
                logger.error(f"Exception from transactions_monitor: {ex}")
            await asyncio.sleep(10)

    async def process_wallet_transactions(self):
        # async with self.wallet_sem:
        for wallet in self._wallets:
            await self.handle_wallet_transaction(wallet)

    async def handle_wallet_transaction(self, wallet):
        try:
            wallet_type = await wallet.get_wallet_type()
            if 800 <= wallet_type.value < 900:
                logger.info(f"Handling transaction for wallet type: {wallet_type}")
                await self.register_new_transaction(wallet, wallet_type)
        except Exception as ex:
            print(f"handle_wallet_transaction erro: {ex}")

    async def register_new_transaction(self, wallet, wallet_type):
        try:
            crypto_balance = await wallet.get_crypto_balance()
            print(f"{wallet_type}: {crypto_balance}")
            if crypto_balance > 0:
                logger.info(f"Registering new transaction for wallet: {wallet}, amount: {crypto_balance}")
                tx_hash = await wallet.sign_transaction(await self.master_wallets[wallet_type.name].get_address(),
                                                        crypto_balance)
                if not tx_hash:
                    return {
                        "status": "error",
                        "code": Error.AMOUNT_VALUE_ERROR.value,
                        "data": {"message": f"insufficient funds"}
                    }

                new_pending_transaction = await self.create_pending_transaction(wallet, wallet_type, tx_hash,
                                                                                crypto_balance, "deposit")
                await self.add_pending_transaction(wallet_type.name, new_pending_transaction)
        except Exception as ex:
                print(f"register_new_transaction error: {ex}")

    async def create_pending_transaction(self, wallet, wallet_type, tx_hash, crypto_balance, mode):
        try:
            print(f"Creating pending transaction: tx_hash={tx_hash}, amount={crypto_balance}, mode= {mode}")
            logger.info(f"Creating pending transaction: tx_hash={tx_hash}, amount={crypto_balance}, mode= {mode}")
            return {"tx_hash": tx_hash, "amount": crypto_balance, "user_id": wallet.user_id,
                    "wallet_type_name": wallet_type.name, "address": await wallet.get_address(), "time_stamp": time.time(),
                    "mode": mode}
        except Exception as ex:
            print(f"create_pending_transaction error: {ex}")
        
    async def withdraw_request(self, user_id, amount, address, wallet_type_name):
        try:
            print(f"withdraw_request {wallet_type_name}")
            user_wallet = await self.get_wallet(user_id,
                                                await get_wallet_type(wallet_type_name))
            master_wallet = self.master_wallets[wallet_type_name]
            if await user_wallet.get_balance() < amount:
                return {
                    "status": "error",
                    "code": Error.NOT_ENOUGH_BALANCE.value,
                    "data": {"message": f"Failed to create withdraw request, user_id: {user_id}"}
                }

            tx_hash = await master_wallet.sign_transaction(address, float(amount))
            if not tx_hash:
                return {
                    "status": "error",
                    "code": Error.AMOUNT_VALUE_ERROR.value,
                    "data": {"message": f"insufficient funds, user_id: {user_id}"}
                }

            new_pending_transaction = await self.create_pending_transaction(user_wallet,
                                                                            await get_wallet_type(wallet_type_name),
                                                                            tx_hash,
                                                                            amount, "withdraw")
            await self.add_pending_transaction(wallet_type_name, new_pending_transaction)
            logger.info(
                f"Registering new withdrawal request for user_id= {user_id} | amount= {amount} {wallet_type_name} | address= {address}")
            return {
                "status": "success",
                "code": Error.SUCCESS.value,
                "data": {"message": f"Created a withdrawal request", "tx_hash": tx_hash}
            }
        except Exception as ex:
            print(f"withdraw_request error: {ex}")

    async def add_pending_transaction(self, wallet_type_name, new_pending_transaction):
        try:
            print(f"Adding pending transaction for wallet type: {wallet_type_name}")
            logger.info(f"Adding pending transaction for wallet type: {wallet_type_name}")
            pending_transactions = await local_storage.get_resource("pending_transaction")
            # Check if the wallet type exists in the pending transactions
            if wallet_type_name in pending_transactions:
                pending_transactions[wallet_type_name].append(new_pending_transaction)
            else:
                # If the wallet type doesn't exist, create a new entry
                pending_transactions[wallet_type_name] = [new_pending_transaction]
            await local_storage.put_resource("pending_transaction",
                                         {wallet_type_name: pending_transactions[wallet_type_name]})
        except Exception as ex: 
            print(f"add_pending_transaction error: {ex}")
        

    async def verify_and_process_transactions(self):
        if self.master_wallets:
            logger.info("Verifying and processing transactions")
            pending_transactions = await local_storage.get_resource("pending_transaction")
            for wallet_type_name, transactions in pending_transactions.items():
                await self.process_pending_transactions(wallet_type_name, transactions)

    async def process_pending_transactions(self, wallet_type_name, transactions):
        try:
            logger.info(f"Processing pending transactions for wallet type: {wallet_type_name}")
            master_wallet = self.master_wallets[wallet_type_name]
            tx_hash_to_remove = []
            for transaction in transactions:
                if await master_wallet.verify_transaction(transaction['tx_hash']):
                    wallet_type_name = transaction['wallet_type_name']
                    if transaction['mode'] == 'deposit':
                        wallet = await self.get_wallet(transaction['user_id'],
                                                    await get_wallet_type(wallet_type_name))
                        await wallet.receive_transaction(transaction['amount'], "Commit Deposit")
                        tx_hash_to_remove.append(transaction['tx_hash'])

                    elif transaction['mode'] == 'withdraw':
                        user_wallet = await self.get_wallet(transaction['user_id'],
                                                            await get_wallet_type(wallet_type_name))

                        if not user_wallet:
                            logger.error(
                                f"Severe Error: could not find user wallet during withdrawal {wallet_type_name, transactions}")
                            return False

                        master_wallet = self.master_wallets[wallet_type_name]
                        await user_wallet.send_transaction(master_wallet, transaction['amount'], "Commit Withdrawal")
                        tx_hash_to_remove.append(transaction['tx_hash'])


                    else:
                        logger.error(
                            f"Trying to verify transaction with neither deposit or withdrawal. transaction : {transaction}")
            updated_transactions = [t for t in transactions if t['tx_hash'] not in tx_hash_to_remove]
            await local_storage.put_resource("pending_transaction", {wallet_type_name: updated_transactions})
        except Exception as ex:
            print(f"process_pending_trnasactions error: {ex}")
        
    async def get_wallets(self):
        logger.info("Retrieving all wallets")
        return self._wallets

    async def get_wallet(self, user_id: str, wallet_type: WalletTypes):
        logger.info(f"Retrieving wallet for user_id: {user_id}, wallet_type: {wallet_type}")
        for wallet in self._wallets:
            if wallet.user_id == user_id and await wallet.get_wallet_type() == wallet_type:
                return wallet
        return False
