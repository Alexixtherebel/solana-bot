import os
import time
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
from telegram import Bot  # For Telegram notifications

load_dotenv()

# ENV variables
PRIVATE_KEY = os.getenv("SOLANA_PRIVATE_KEY")
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Initialize Solana client
client = Client(RPC_URL)

# Initialize Telegram bot if credentials exist
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID else None

# Helper: load keypair from the private key
def load_keypair_from_env():
    key_bytes = [int(x) for x in PRIVATE_KEY.strip("[]").split(",")]
    return Keypair.from_bytes(bytes(key_bytes))

# Send Telegram notification
def send_telegram_message(message: str):
    if telegram_bot:
        try:
            telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        except Exception as e:
            print("Failed to send Telegram message:", e)

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
    send_telegram_message(f"Sent {amount_sol} SOL to {destination}. Result: {result}")

# Test loop
def test_loop():
    print("Starting test loop... (updates every 60 seconds)")
    send_telegram_message("Bot started: running Solana slot test loop.")
    for i in range(10):
        print(f"[{i+1}/10] Checking Solana slot...")
        try:
            slot = client.get_slot()
            print("Current Solana slot:", slot)
            send_telegram_message(f"[{i+1}/10] Solana slot: {slot}")
        except Exception as e:
            print("Error fetching slot:", e)
            send_telegram_message(f"Error fetching slot: {e}")
        print("-" * 50)
        time.sleep(60)
    print("Test loop complete. Bot shutting down.")
    send_telegram_message("Test loop complete. Bot shutting down.")

if __name__ == "__main__":
    print("Bot started successfully! Ready to run actions.")
    print("Fetching Solana slot as a quick test...")

    try:
        slot = client.get_slot()
        print("Current Solana slot:", slot)
    except Exception as e:
        print("Error fetching slot:", e)

    print("Bot test complete.")
    # Run the 10-minute Telegram test loop
    test_loop()
