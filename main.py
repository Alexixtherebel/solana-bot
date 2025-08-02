import os
from dotenv import load_dotenv
from solders.keypair import Keypair
from solders.system_program import TransferParams, transfer
from solana.rpc.api import Client

# Load environment variables
load_dotenv()

# RPC endpoint and private key from .env
RPC_ENDPOINT = os.getenv("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
PRIVATE_KEY = os.getenv("SOLANA_PRIVATE_KEY")
RECIPIENT = os.getenv("RECIPIENT_WALLET")
LAMPORTS = int(float(os.getenv("AMOUNT_SOL", "0.03")) * 1_000_000_000)

# Initialize Solana client
client = Client(RPC_ENDPOINT)

def load_keypair_from_private_key(private_key_str: str) -> Keypair:
    """Convert a JSON array string of 64 integers into a Keypair."""
    import json
    key_data = json.loads(private_key_str)
    return Keypair.from_bytes(bytes(key_data))

def main():
    print("Starting Solana bot...")

    # Load sender keypair
    keypair = load_keypair_from_private_key(PRIVATE_KEY)
    sender_pubkey = keypair.pubkey()
    recipient_pubkey = RECIPIENT

    print(f"Preparing to send {LAMPORTS / 1_000_000_000} SOL from {sender_pubkey} to {recipient_pubkey}")

    # Create transfer transaction
    params = TransferParams(
        from_pubkey=sender_pubkey,
        to_pubkey=recipient_pubkey,
        lamports=LAMPORTS
    )
    txn = transfer(params)

    # Send transaction
    try:
        response = client.send_transaction(txn, keypair)
        print("Transaction sent!")
        print(response)
    except Exception as e:
        print("Error while sending transaction:", str(e))

if __name__ == "__main__":
    main()
