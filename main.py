import os
import time
import requests
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
from bs4 import BeautifulSoup

load_dotenv()

# ENV variables
PRIVATE_KEY = os.getenv("SOLANA_PRIVATE_KEY")
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Initialize Solana client
client = Client(RPC_URL)

# Helper: load keypair from the private key
def load_keypair_from_env():
    key_bytes = [int(x) for x in PRIVATE_KEY.strip("[]").split(",")]
    return Keypair.from_bytes(bytes(key_bytes))

# Send a Telegram message using HTTP API (no async issues)
def send_telegram_message(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured, skipping notification.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"Failed to send Telegram message: {r.text}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

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
    send_telegram_message("🚀 Bot started successfully and is ready to run actions!")

    # Test loop
    print("Starting test loop with Telegram notifications for each slot...")
    for i in range(1, 4):  # 3 iterations
        try:
            slot = client.get_slot()
            msg = f"[{i}/3] Current Solana slot: {slot}"
            print(msg)
            send_telegram_message(msg)
        except Exception as e:
            err_msg = f"Error fetching slot on iteration {i}: {e}"
            print(err_msg)
            send_telegram_message(err_msg)

        time.sleep(60)  # Wait 60 seconds between iterations

    print("Test loop complete. Bot shutting down.")
    send_telegram_message("✅ Test loop complete. Bot shutting down.")
