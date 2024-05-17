from enum import Enum


class WalletCategories(Enum):
    CRYPTO = "Crypto"
    DEMO = "Demo"


class WalletTypes(Enum):
    DEMO = 1
    ETH = 801
    BNB = 802
    SOL = 803


async def get_wallet_type(wallet_type_name):
    try:
        return getattr(WalletTypes, wallet_type_name)
    except AttributeError:
        print(f"Wallet type '{wallet_type_name}' is not a valid WalletTypes member.")
        return None