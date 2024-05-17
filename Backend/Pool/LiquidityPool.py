from collections import deque
from Databases.Remote.RemoteStorage import RemoteStorage
from Logger.CustomLogger import CustomLogger
from Wallets.WalletTypes import WalletTypes, get_wallet_type
from Wallets.WalletsFactory import WalletsFactory

logger = CustomLogger.get_instance()
db = RemoteStorage.get_storage()


class LiquidityPool:
    def __init__(self):
        self._wallets = None
        self.payment_queue = deque()  # Initialize the payment queue with an empty deque

    def set_wallets(self, wallets):
        self._wallets = wallets
        return True

    async def _init(self):
        pool_data = await db.get({"path": "LiquidityPool/Data"})
        if pool_data is None or 'queue' not in pool_data:
            # If there's no data, or 'queue' key is not in the data, initialize with an empty list
            await db.post({"path": "LiquidityPool/Data", "data": {"queue": []}})
            self.payment_queue = deque()
        else:
            # If there is data, convert the list of dicts to a deque
            self.payment_queue = deque([(item['user_id'], item['wallet_type'], item['amount'], item['description'])
                                       for item in pool_data['queue']])
        return True

    async def get_wallet(self, type_: WalletTypes):
        for wallet in self._wallets:
            if await wallet.get_wallet_type() == type_:
                return wallet
        return False

    async def process_payment_queue(self):
        try:
            while self.payment_queue:
                user_id, wallet_type_name, amount, description = self.payment_queue[0]  # Get the first request in the queue
                user_wallet = await WalletsFactory.create_wallet(await get_wallet_type(wallet_type_name), user_id)
                if not user_wallet:
                    logger.error(f"Payment failed:  {user_id}, {wallet_type_name}, {amount}, {description}")
                    break  # Stop processing if a payment fails

                wallet_type = await user_wallet.get_wallet_type()
                pool_wallet = await self.get_wallet(wallet_type)

                result = await pool_wallet.send_transaction(user_wallet, amount, description)
                if result:
                    logger.info(f"Payment successful: {user_id}, {wallet_type_name}, {amount}, {description}")
                    self.payment_queue.popleft()  # Remove the request from the queue if payment is successful
                    await self.back_up_queue()
                else:
                    logger.error(f"Payment failed:  {user_id}, {wallet_type_name}, {amount}, {description}")
                    break  # Stop processing if a payment fails    
        except Exception as ex:
            print(f"process_payment_queue ex: {ex}")
    async def request_payment_from_pool(self, user_id, wallet_type: WalletTypes, amount: float, description=None):
        """
        User request to get payment from the pool.
        """
        wallet_type_name = wallet_type.name
        self.payment_queue.append((user_id, wallet_type_name, amount, description))  # Add the payment request to the queue
        await self.back_up_queue()
        await self.process_payment_queue()  # Process the queue

    async def send_payment_to_pool(self, user_id, wallet_type: WalletTypes, amount: float, description=None):
        """
        User sends payment to the pool.
        """
        pool_wallet = await self.get_wallet(wallet_type)
        user_wallet = await WalletsFactory.create_wallet(wallet_type, user_id)

        result = await user_wallet.send_transaction(pool_wallet, amount, description)
        await self.process_payment_queue()
        return result

    async def to_dict(self):
        # Convert each payment request in the queue to a dictionary
        queue_list = [{"user_id": user_id,
                       "wallet_type": wallet_type,
                       "amount": amount,
                       "description": description} for user_id, wallet_type, amount, description in self.payment_queue]

        # Convert wallets to a dictionary
        wallets_dict = {(await wallet.get_wallet_type()).name: await wallet.to_dict() for wallet in self._wallets}

        # Combine everything into the final state dictionary
        result = {
            "queue": queue_list,
            "wallets": wallets_dict
        }
        return result

    async def back_up_queue(self):
        try:
            # Get the queue in list of dictionaries format
            queue_list = [{"user_id": user_id,
                        "wallet_type": wallet_type,
                        "amount": amount,
                        "description": description} for user_id, wallet_type, amount, description in self.payment_queue]

            # Update the queue in the database
            await db.update({"path": "LiquidityPool/Data", "data": {"queue": queue_list}})
            return True
        except Exception as ex: 
            print(f"back_up_queue")
       
