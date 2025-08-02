import os
import time
import json
from solana.rpc.api import Client
from solana.keypair import Keypair
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Solana Bot Started Successfully ===")
print("Connecting to Solana network...")

# Connect to Solana devnet (you can switch to mainnet if ready)
client = Client("https://api.devnet.solana.com")

# Get private key from environment variable
private_key = os.getenv("SOLANA_PRIVATE_KEY")

if not private_key:
    print("ERROR: SOLANA_PRIVATE_KEY is not set.")
    exit(1)

try:
    # Decode the private key (assuming JSON array format)
    secret_key = json.loads(private_key)
    keypair = Keypair.from_secret_key(bytes(secret_key))
    print("Wallet loaded successfully.")
except Exception as e:
    print(f"Failed to load keypair: {e}")
    exit(1)

# Simple example: check SOL balance
try:
    balance = client.get_balance(keypair.public_key)
    print(f"Current wallet balance: {balance['result']['value']} lamports")
except Exception as e:
    print(f"Error fetching balance: {e}")

print("Bot is running. Waiting for market signals...")

# Keep the bot running and printing heartbeats
while True:
    print("Heartbeat: Bot is alive.")
    time.sleep(30)
