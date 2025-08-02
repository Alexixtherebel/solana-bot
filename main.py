import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Solana + Solders libraries
from solders.keypair import Keypair
from solders.system_program import TransferParams, transfer
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solana.transaction import Transaction
from solders.pubkey import Pubkey

# Other libraries
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

PRIVATE_KEY = os.getenv("SOLANA_PRIVATE_KEY")
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

# Initialize Solana client
client = Client(RPC_URL)

# Helper: load keypair from the private key
def load_keypair_from_env():
    key_bytes = [int(x) for x in PRIVATE_KEY.strip("[]").split(",")]
    return Keypair.from_bytes(bytes(key_bytes))

# Example: simple transfer function
def send_sol(destination: str, amount_sol: float):
    sender = load_keypair_from_env()
    dest_pubkey = Pubkey.from_string(destination)

    lamports = int(amount_sol * 1_000_000_000)

    txn = Transaction().add(
        transfer(
            TransferParams(
                from_pubkey=sender.pubkey(),
                to_pubkey=dest_pubkey,
                lamports=lamports,
            )
        )
    )

    result = client.send_transaction(txn, sender, opts=TxOpts(skip_preflight=True))
    print("Transaction result:", result)

# Health check: fetch current slot
def fetch_slot():
    try:
        slot = client.get_slot()
        return slot
    except Exception as e:
        print("Error fetching slot:", e)
        return None

if __name__ == "__main__":
    print("Bot started successfully! Ready to run actions.")
    print("Starting automatic loop... (updates every 60 seconds)\n")

    while True:
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"[{current_time}] Checking Solana slot...")

        slot = fetch_slot()
        if slot:
            print(f"[{current_time}] Current Solana slot: {slot}")
        else:
            print(f"[{current_time}] Failed to fetch slot.")

        print("-" * 50)
        time.sleep(60)  # Wait 60 seconds before the next check
