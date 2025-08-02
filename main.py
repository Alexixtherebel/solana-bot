import os
import time
from dotenv import load_dotenv

# Solana + Solders
from solders.keypair import Keypair
from solders.system_program import TransferParams, transfer
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solana.transaction import Transaction
from solders.pubkey import Pubkey

# Notifications
import requests

load_dotenv()

# ENV variables
PRIVATE_KEY = os.getenv("SOLANA_PRIVATE_KEY")
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

client = Client(RPC_URL)

# Telegram notification helper
def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except Exception as e:
        print("Failed to send Telegram message:", e)

# Load keypair from ENV
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

    try:
        result = client.send_transaction(txn, sender, opts=TxOpts(skip_preflight=True))
        msg = f"Transaction sent successfully: {result}"
        print(msg)
        send_telegram(msg)
    except Exception as e:
        err = f"Error sending transaction: {e}"
        print(err)
        send_telegram(err)

if __name__ == "__main__":
    print("Bot started successfully! Ready to run actions.")
    send_telegram("🚀 Bot started successfully and is now running.")

    # Main test loop (10 iterations)
    print("Starting test loop... (updates every 60 seconds)")
    for i in range(10):
        try:
            slot = client.get_slot()
            print(f"[{i+1}/10] Solana slot: {slot}")
        except Exception as e:
            err = f"Error fetching slot: {e}"
            print(err)
            send_telegram(err)

        time.sleep(60)

    print("Test loop complete. Bot shutting down.")
    send_telegram("✅ Test loop complete. Bot shutting down.")
