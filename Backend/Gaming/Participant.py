import time

from Gaming.Odd import Odd
from Wallets.WalletsFactory import WalletTypes


class Participant:
    def __init__(self, user_id, market_key_id, odd: Odd, amount: float, wallet_type: WalletTypes, bet_time=None):
        self.user_id = user_id
        self.wallet_type = wallet_type
        self.market_key_id = market_key_id
        self.odd = odd
        self.amount = amount
        if bet_time is None:
            self.bet_time = time.time()
        else:
            self.bet_time=bet_time

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "wallet_type": self.wallet_type.value,  # Assuming WalletTypes is an Enum or has a value attribute
            "market_key_id": self.market_key_id,
            "odd": self.odd.to_dict(),
            "amount": self.amount,
            "bet_time": self.bet_time
        }
