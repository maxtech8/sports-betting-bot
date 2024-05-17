import asyncio

from Databases.Remote.RemoteStorage import RemoteStorage
from Logger.CustomLogger import CustomLogger
from Pool.LiquidityPool import LiquidityPool
from Wallets.WalletTypes import WalletTypes
from Wallets.WalletsFactory import WalletsFactory

logger = CustomLogger.get_instance()
db = RemoteStorage.get_storage()


class PoolFactory:

    @staticmethod
    async def create_pool():
        # Initialize the pool
        pool = LiquidityPool()
        tasks = [WalletsFactory.create_wallet(type_, "pool") for type_ in WalletTypes]
        user_wallets = await asyncio.gather(*tasks)
        pool.set_wallets(user_wallets)
        await pool._init()
        return pool

# async def main():
#
#     pool_wallet = await pool.get_wallet(WalletTypes.DEMO)
#     await pool_wallet.receive_transaction(5000)
#     await pool.request_payment_from_pool("test", WalletTypes.DEMO, 10, "Win bet")
#     print(await pool_wallet.to_dict())
#     print(pool.payment_queue)
