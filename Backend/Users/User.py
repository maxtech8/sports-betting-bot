from Wallets.WalletsFactory import WalletTypes


class User:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self._terms_and_conditions_approved = False
        self._wallets = []

    async def get_all_wallets(self):
        return self._wallets

    async def get_wallet(self, type_: WalletTypes):
        for wallet in self._wallets:
            if await wallet.get_wallet_type() == type_:
                return wallet
        return False

    async def set_terms_and_conditions_approved(self, approval=False):
        self._terms_and_conditions_approved = approval

    async def get_terms_and_conditions_approved(self):
        return self._terms_and_conditions_approved

    async def to_dict(self):
        return {
            "user_id": self.user_id,
            "terms_and_conditions_approved": self._terms_and_conditions_approved,
            "wallets": [await wallet.to_dict() for wallet in self._wallets],
        }

    async def set_wallets(self, wallets: list):
        self._wallets = wallets

    async def get_wallets(self, wallets: list):
        self._wallets = wallets
