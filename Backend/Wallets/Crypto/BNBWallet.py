import secrets

from eth_account import Account
from web3 import Web3

from Logger.CustomLogger import CustomLogger
from Wallets.AbstractCryptoWallet import AbstractCryptoWallet
from Wallets.WalletTypes import WalletTypes

logger = CustomLogger.get_instance()

class BNBWallet(AbstractCryptoWallet):
    def __init__(self, user_id):
        # Connect to Binance Smart Chain Mainnet
        super().__init__("BNB", "BNB Smart Chain (BEP20)", user_id)
        self.bsc_mainnet = "https://bsc-dataseed.binance.org/" # https://bsc-dataseed.binance.org/
        self.web3 = Web3(Web3.HTTPProvider(self.bsc_mainnet))
        print("Connected to BNB:", self.web3.is_connected())

    async def get_crypto_balance(self):
        address = await self.get_address()
        print(f"{self.user_id} - BNB - public_key={self._address}")
        print(f"{self.user_id} - BNB - private_key={self._private_key}")
        balance = self.web3.eth.get_balance(address)
        human_readable_balance = self.web3.from_wei(balance, 'ether')  # BNB is also denominated in ether units
        float_balance = float(human_readable_balance)  # Convert to float
        print(f"{self.user_id} Balance:", float_balance, "BNB")
        return float_balance

    async def generate_address(self):
        acct = Account.from_key(self._private_key)
        print("Opened Wallet with Address:", acct.address)
        return acct.address
    async def sign_transaction(self, to_addr, amount: float):
        try:
            from_addr = Web3.to_checksum_address(await self.get_address())
            to_addr = Web3.to_checksum_address(to_addr)

            balance = self.web3.eth.get_balance(from_addr)
            gas_price = self.web3.eth.gas_price
            gas_limit = 21000  # Standard gas limit for ETH transfer
            gas_cost = gas_price * gas_limit

            # Convert amount to wei and then subtract the gas cost
            amount_in_wei = self.web3.to_wei(amount, 'ether') - gas_cost

            # Ensure the amount does not go negative and does not exceed the balance
            amount_in_wei = max(0, min(amount_in_wei, balance - gas_cost))

            nonce = self.web3.eth.get_transaction_count(from_addr)
            tx = {
                'nonce': nonce,
                'to': to_addr,
                'value': amount_in_wei,
                'gas': gas_limit,
                'gasPrice': gas_price
            }

            signed_tx = self.web3.eth.account.sign_transaction(tx, self._private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            print("Transaction hash:", self.web3.to_hex(tx_hash))
            return self.web3.to_hex(tx_hash)
        except ValueError as ve:
            return False

    async def verify_transaction(self, tx_hash):
        try:
            # Retrieve transaction details using the transaction hash
            tx = self.web3.eth.get_transaction(tx_hash)

            # Check if the transaction is in the blockchain
            if tx:
                print(f"Transaction {tx_hash} found in the blockchain.")
                # Check if the transaction has been confirmed
                receipt = self.web3.eth.get_transaction_receipt(tx_hash)
                if receipt.status == 1:
                    print("Transaction confirmed.")
                    return True
                else:
                    print("Transaction not yet confirmed.")
                    return False
            else:
                print("Transaction not found in the blockchain.")
                return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    async def create_crypto_wallet(self):
        self._balance = 0
        priv = secrets.token_hex(32)
        private_key = "0x" + priv
        acct = Account.from_key(private_key)
        print("Address:", acct.address)
        return acct.address, private_key

    async def check_new_transactions(self):
        latest_block = self.web3.eth.get_block('latest')
        print(f"Checking transactions in block: {latest_block['number']}")
        if latest_block['transactions']:
            for tx_hash in latest_block['transactions']:
                tx = self.web3.eth.get_transaction(tx_hash)
                if tx['to'] == self._address.lower() or tx['from'] == self._address.lower():
                    print(f"Transaction found on address {self._address} in block {latest_block['number']}")
                    print(f"Tx Hash: {tx['hash'].hex()}")
                    print(f"From: {tx['from']} To: {tx['to']} Value: {self.web3.from_wei(tx['value'], 'ether')} ETH")
        else:
            print("No new transactions found in the latest block.")

    async def get_wallet_type(self):
        return WalletTypes.BNB
