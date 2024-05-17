#
import secrets
from web3 import Web3
from solders.keypair import Keypair # type: ignore
from solders.pubkey import Pubkey # type: ignore

from Logger.CustomLogger import CustomLogger
from Wallets.AbstractCryptoWallet import AbstractCryptoWallet
from Wallets.WalletTypes import WalletTypes
from jupiter_python_sdk.jupiter import Jupiter

from solana.rpc.api import Client
from solana.transaction import Transaction
from solders.system_program import TransferParams, transfer
from solana.rpc.types import TxOpts
import struct

from solders.signature import Signature # type: ignore

import base58

logger = CustomLogger.get_instance()


class SOLWallet(AbstractCryptoWallet):
    def __init__(self, user_id):
        try:
            # Connect to Solana Mainnet
            super().__init__("SOL", "Solana", user_id)
            self.client = Client("https://api.mainnet-beta.solana.com") # https://api.mainnet-beta.solana.com
            self.solWallet = None
            # self.rpc_end_point = f"https://solana-testnet.g.alchemy.com/v2/E2OfmKl0-3bIlP6j8B0lI7JkjxUHOm_r"  # Replace with your Infura Project ID
            # self.web3 = Web3(Web3.HTTPProvider(self.rpc_end_point))
            print("Connected to SOL:", self.client.is_connected())
            
        except Exception as e:
            print(f"Error: {e}")

    async def get_crypto_balance(self):
        try:
            print(f"{self.user_id} - SOL - public_key = {self._address}")
            print(f"{self.user_id} - SOL - private_key = {self._private_key}")
            decoded = base58.b58decode(f"{self._private_key}")
            self.solWallet = Keypair.from_bytes(decoded)
            balance = self.get_sol_balance()
            float_balance = float(balance)
            print(f"{self.user_id} - SOL - Balance:", float_balance, "SOL")
            return float_balance
        except ValueError as e:
            print(f"Error: {e}")
            
    async def generate_address(self):
        acct = Keypair.from_bytes(base58.b58decode(f"{self._private_key}"))
        print("Opened Wallet with Address:", acct.pubkey())
        print(f"generated sol address {acct.pubkey()}")
        return str(acct.pubkey())

    def get_sol_balance(self):
        response = self.client.get_balance(pubkey = self.solWallet.pubkey())
        balance = float(response.value) / 10 ** 9
        return balance
    
    async def sign_transaction(self, to_addr, amount: float):
        try:
            self.solWallet = Keypair.from_bytes(base58.b58decode(f"{self._private_key}"))
            from_addr = await self.get_address()
            print(f"from_address = {from_addr}")
            print(f"sender = {self.solWallet.pubkey()}")
            print(f"receiver = {to_addr}")
            balance = self.get_sol_balance()
            print(f"wallet balance = {balance}")
            print(f"database balance = {self._balance}")
            
            sender_keypair = self.solWallet
            receiver = Pubkey.from_string(to_addr)
            amount_wei = int(amount * 10**9)  # Amount to transfer
            transaction_fee = 0.000005
            total_lamports = amount_wei - int(transaction_fee * 10 ** 9)
            print(f"total_lamports = {total_lamports}")
            # program_id=Pubkey.from_string('11111111111111111111111111111111')
            txn = (Transaction()
                # .add(set_compute_unit_price(10000))
                .add(
                    transfer(
                        TransferParams(
                            from_pubkey=sender_keypair.pubkey(), 
                            to_pubkey=receiver, 
                            lamports = total_lamports
                        )
                    )
            ))
            print(f"txn = {txn}")
            # Sign transaction
            # txn.sign(sender_keypair)
            
            # amount_hex=struct.pack('<Q', amount).hex()
            # data='02000000'+amount_hex
            # data_bytes=bytes.fromhex(data)
            # accounts=[
            #     AccountMeta(sender_keypair.pubkey(),True,True),
            #     AccountMeta(receiver,False,True)
            # ]           
            # transfer_ix=Instruction(program_id,data_bytes,accounts)
            # print(transfer_ix)
            
            # transaction = Transaction()
            # txn = transaction.add(transfer_ix)
            # hash=self.client.send_transaction(txn, sender_keypair)
            # print('Transactionhash:', hash.value)
            estimateFee = self.client.get_fee_for_message(txn.compile_message()).value
            print(f"estimateFee = {estimateFee}")
            txResp = self.client.send_transaction(txn, sender_keypair, opts=TxOpts(skip_confirmation=False))
            txHash = txResp.value
            print(f"txHash = {txHash}")
            status = self.client.confirm_transaction(tx_sig=txHash)
            print (status)
            return str(txHash)
        except Exception as e:
            print(f"sign_transaction: {e}")

    async def verify_transaction(self, tx_hash):
        try:
            print(f"verify_transaction({tx_hash})")
            # Retrieve transaction details using the transaction hash
            tx_status = self.client.get_signature_statuses([Signature.from_string(tx_hash)])
            print(f"tx_status = {tx_status}")
            
            # Check if the transaction is in the blockchain
            if tx_status:
                print(tx_status.value)
                print(f"Transaction {tx_hash} found in the blockchain.")
                # Check if the transaction has been confirmed
                status = tx_status.value[0]
                if status is None:
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
        #Generate a new keypair
        keypair = Keypair()
        rawPrivateKey = bytes(keypair)
        private_key = keypair.from_base58_string(base58.b58encode(rawPrivateKey).decode())
        public_key = keypair.pubkey()
        print(f"new_private_key = {type(private_key)}, public_key = {public_key, type(public_key)}")
        return str(public_key), str(private_key)

    async def check_new_transactions(self):
        try:
            # Fetch the latest block
            latest_block = (await self.get_recent_blockhash())["result"]["value"]["blockhash"]
            print(f"Checking transactions in block: {latest_block['number']}")

            # Fetch transactions in the latest block
            block_transactions = (await self.client.get_confirmed_block(latest_block))["result"]["value"]["transactions"]
            
            if block_transactions:
                for tx in block_transactions:
                    # Check if the transaction involves the specified address
                    if self.address in [tx["transaction"]["message"]["accountKeys"][i] for i in [0, 1]]:
                        print(f"Transaction found involving address {self.address} in block {latest_block}")
                        print(f"Tx Hash: {tx['transaction']['signatures'][0]}")
                        print("From:", tx["meta"]["preTokenBalances"][0]["source"] if tx["meta"]["preTokenBalances"] else "Unknown")
                        print("To:", tx["meta"]["postTokenBalances"][0]["source"] if tx["meta"]["postTokenBalances"] else "Unknown")
                        print("Value:", tx["meta"]["postTokenBalances"][0]["postAmount"] if tx["meta"]["postTokenBalances"] else "Unknown")
            else:
                print("No new transactions found in the latest block.")
        
        except Exception as e:
            print(f"An error occurred: {e}")

    async def get_wallet_type(self):
        return WalletTypes.SOL
    
    async def get_recent_blockhash(self):
        try:
            # Fetch the recent block hash
            response = await self.client.request("getRecentBlockhash", params=[])
            return response["result"]["value"]["blockhash"]
        except Exception as e:
            print(f"An error occurred while fetching recent block hash: {e}")
            return None
