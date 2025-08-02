import os
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
import time

load_dotenv()

# ENV variables
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

if __name__ == "__main__":
    print("Bot started successfully! Ready to run actions.")

    # ---- TEST BLOCK ----
    try:
        print("Fetching Solana slot as a quick test...")
        slot = client.get_slot()
        print("Current Solana slot:", slot)
    except Exception as e:
        print("Error fetching slot:", e)
    # ---------------------

    # Keep bot alive briefly (simulate long-running)
    time.sleep(5)
    print("Bot test complete.")
