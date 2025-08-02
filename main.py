import os
from dotenv import load_dotenv
import asyncio

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

# Telegram (aiogram)
from aiogram import Bot

load_dotenv()

# ENV variables
PRIVATE_KEY = os.getenv("SOLANA_PRIVATE_KEY")
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Initialize Solana client
client = Client(RPC_URL)
bot = Bot(token=TELEGRAM_BOT_TOKEN)


# Helper: load keypair from the private key
def load_keypair_from_env():
    key_bytes = [int(x) for x in PRIVATE_KEY.strip("[]").split(",")]
    return Keypair.from_bytes(bytes(key_bytes))


# Async function to send Telegram messages
async def send_telegram_message(text: str):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
    except Exception as e:
        print("Failed to send Telegram message:", e)


def notify(text: str):
    # Wrap async call
    asyncio.run(send_telegram_message(text))


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
    notify(f"Transaction sent!\nResult: {result}")


if __name__ == "__main__":
    print("Bot started successfully! Ready to run actions.")
    notify("🚀 Bot started successfully and is ready to run actions.")

    # Test: Fetch slot 3 times
    print("Starting test loop with Telegram notifications for each slot...")
    for i in range(3):
        try:
            slot = client.get_slot()
            msg = f"[{i+1}/3] Current Solana slot: {slot}"
            print(msg)
            notify(msg)
        except Exception as e:
            error_msg = f"Error fetching slot: {e}"
            print(error_msg)
            notify(error_msg)

    print("Test loop complete. Bot shutting down.")
    notify("✅ Test loop complete. Bot shutting down.")
