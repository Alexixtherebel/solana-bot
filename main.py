import os
from solders.keypair import Keypair
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to Solana
client = Client("https://api.mainnet-beta.solana.com")

# Load private key from environment variable
private_key_str = os.getenv("SOLANA_PRIVATE_KEY")
if not private_key_str:
    raise Exception("SOLANA_PRIVATE_KEY not found in environment variables!")

# Convert private key string to list of ints
private_key = [int(x) for x in private_key_str.split(",")]
keypair = Keypair.from_bytes(bytes(private_key))

print("Bot started successfully! Wallet public key:", keypair.pubkey())

# Example logic: check balance
balance = client.get_balance(keypair.pubkey())
print("Current balance:", balance.value)

# Example logic: trade placeholder
# Replace with your trading logic
print("Ready to trade with 0.04 SOL per trade...")
