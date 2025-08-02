import requests
from bs4 import BeautifulSoup
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np
from solana.rpc.api import Client
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import Transaction
from solders.pubkey import Pubkey
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
import base58
import time
import aiohttp
import asyncio
import tweepy
from datetime import datetime
import os
from dotenv import load_dotenv

# ===============================
# PAPER MODE FLAG
PAPER_MODE = True
print("\n*** BOT IS IN PAPER MODE - NO REAL TRADES WILL BE EXECUTED ***\n")
# ===============================

# Load environment variables
load_dotenv()
SOLANA_PRIVATE_KEY = os.getenv('SOLANA_PRIVATE_KEY')  # Base58-encoded private key

# Solana RPC client
SOLANA_CLIENT = Client("https://api.mainnet-beta.solana.com")

# Wallet setup
if SOLANA_PRIVATE_KEY:
    try:
        keypair = Keypair.from_bytes(base58.b58decode(SOLANA_PRIVATE_KEY))
        WALLET_ADDRESS = keypair.pubkey()
    except Exception as e:
        raise ValueError(f"Invalid SOLANA_PRIVATE_KEY: {e}")
else:
    raise ValueError("SOLANA_PRIVATE_KEY not set in .env")

# Constants
BUY_AMOUNT_SOL = 0.03 * 1_000_000_000  # 0.03 SOL (~$5) in lamports
SLIPPAGE_BPS = 300  # 3%
PRIORITY_FEE_MICRO_LAMPORTS = 5_000
COMPUTE_UNITS = 200_000

# Twitter API Setup (replace with your credentials)
CONSUMER_KEY = 'your_consumer_key'
CONSUMER_SECRET = 'your_consumer_secret'
ACCESS_TOKEN = 'your_access_token'
ACCESS_TOKEN_SECRET = 'your_access_token_secret'

auth = tweepy.OAuth1UserHandler(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
twitter_api = tweepy.API(auth)

# Simulated historical data for ML
SIMULATED_DATA = np.array([
    [100000, 500000, 200000, 5.0, 20.0, 1000, 80],
    [50000, 1000000, 100000, 2.0, 10.0, 500, 50],
    [20000, 2000000, 50000, -1.0, 5.0, 200, 20],
])
X_sim = SIMULATED_DATA[:, :-1]
y_sim = SIMULATED_DATA[:, -1]
X_train, X_test, y_train, y_test = train_test_split(X_sim, y_sim, test_size=0.2)
scaler = StandardScaler().fit(X_train)
model = RandomForestRegressor(n_estimators=100).fit(scaler.transform(X_train), y_train)

# Blacklist
RUGGER_BLACKLIST = ["RuggerWallet1SoL...abc","CabalGroupWallet2SoL...def"]

async def fetch_dexscreener_price(token_address):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.dexscreener.com/latest/dex/pairs/solana/{token_address}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return float(data['pairs'][0]['priceUsd']) if data['pairs'] else None
        return None
    except Exception as e:
        print(f"Dexscreener error: {e}")
        return None

def fetch_solsniffer_score(token_address):
    url = f"https://api.solsniffer.com/score/{token_address}"  # Hypothetical
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get('score', 0)
        return 0
    except Exception as e:
        print(f"SolSniffer error for {token_address}: {e}")
        return 0

def detect_fake_volume(token_address):
    try:
        signatures = SOLANA_CLIENT.get_signatures_for_address(Pubkey.from_string(token_address), limit=100).value
        if not signatures:
            return False
        unique_signers = set()
        txn_count = len(signatures)
        for sig in signatures:
            txn = SOLANA_CLIENT.get_transaction(sig.signature, max_supported_transaction_version=0).value
            if txn:
                for key in txn.transaction.message.account_keys:
                    unique_signers.add(str(key))
        unique_count = len(unique_signers)
        return unique_count < (txn_count * 0.05)
    except Exception as e:
        print(f"Fake volume check error for {token_address}: {e}")
        return False

def check_rugger_deployer(token_address):
    try:
        accounts = SOLANA_CLIENT.get_program_accounts(
            Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
            filters=[{"memcmp": {"offset": 0, "bytes": token_address}}]
        )
        if not accounts.value:
            return False
        mint_account = accounts.value[0].pubkey
        signatures = SOLANA_CLIENT.get_signatures_for_address(mint_account, limit=1).value
        if signatures:
            txn = SOLANA_CLIENT.get_transaction(signatures[0].signature).value
            if txn:
                deployer = str(txn.transaction.message.account_keys[0])
                return deployer in RUGGER_BLACKLIST
        return False
    except Exception as e:
        print(f"Rugger check error for {token_address}: {e}")
        return False

def fetch_pump_fun_data():
    url = "https://www.pump.fun/board"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        coins = []
        for row in soup.select('table tr')[1:10]:
            cols = row.select('td')
            if cols:
                name = cols[0].text.strip()
                market_cap = float(cols[1].text.strip().replace('$', '').replace(',', ''))
                volume = float(cols[2].text.strip().replace('$', '').replace(',', ''))
                coins.append({'name': name, 'market_cap': market_cap, 'volume': volume, 'source': 'pump.fun'})
        return coins
    except Exception as e:
        print(f"Pump.fun fetch error: {e}")
        return []

def fetch_meteora_data():
    url = "https://api.meteora.ag/pools"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            coins = []
            for pool in data[:10]:
                token = pool['tokenA']['symbol']
                liquidity = pool['liquidity']
                volume = pool['volume24h']
                coins.append({'name': token, 'liquidity': liquidity, 'volume': volume, 'source': 'meteora.ag'})
            return coins
        return []
    except Exception as e:
        print(f"Meteora fetch error: {e}")
        return []

def fetch_letsbonk_data():
    url = "https://www.letsbonk.fun/"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        coins = []
        for item in soup.select('.coin-item')[:10]:
            name = item.select_one('.name').text.strip()
            price = float(item.select_one('.price').text.strip().replace('$', ''))
            holders = int(item.select_one('.holders').text.strip())
            coins.append({'name': name, 'price': price, 'holders': holders, 'source': 'letsbonk.fun'})
        return coins
    except Exception as e:
        print(f"Letsbonk fetch error: {e}")
        return []

def enrich_with_solana_data(coin):
    return {'supply': 1000000000}

def evaluate_twitter(handle):
    try:
        user = twitter_api.get_user(screen_name=handle)
        created_at = user.created_at
        account_age_days = (datetime.now() - created_at).days
        follower_count = user.followers_count
        tweet_count = user.statuses_count
        verified = user.verified
        followers = twitter_api.get_followers(screen_name=handle, count=100)
        notable_followers = [f.screen_name for f in followers if (f.verified or f.followers_count > 10000)]
        notable_count = len(notable_followers)
        trust_score = 0
        if account_age_days > 365: trust_score += 30
        if verified: trust_score += 20
        trust_score += min(follower_count / 1000, 30)
        if tweet_count > 1000: trust_score += 10
        if account_age_days < 180 and follower_count > 5000: trust_score -= 20
        reused_flag = account_age_days < 180 and tweet_count < 100
        return {
            'notable_followers_count': notable_count,
            'notable_followers_list': notable_followers[:5],
            'trust_score': max(0, min(100, trust_score)),
            'reused_flag': reused_flag
        }
    except tweepy.errors.TweepyException as e:
        print(f"Twitter error for {handle}: {e}")
        return {'notable_followers_count': 0, 'notable_followers_list': [], 'trust_score': 0, 'reused_flag': False}

def analyze_profitability(coins_df):
    try:
        features = coins_df[['volume', 'market_cap', 'liquidity', 'price_change_1h', 'price_change_24h', 'holders']].fillna(0)
        scaled_features = scaler.transform(features)
        scores = model.predict(scaled_features)
        coins_df['profitability_score'] = scores
        coins_df['profitability_score'] += (coins_df['volume'] / (coins_df['market_cap'] + 1)) * 10
        coins_df['profitability_score'] *= (coins_df['trust_score'] / 100)
        coins_df.loc[coins_df['reused_flag'], 'profitability_score'] *= 0.8
        return coins_df.sort_values('profitability_score', ascending=False)
    except Exception as e:
        print(f"Analysis error: {e}")
        return pd.DataFrame()

async def get_jupiter_quote(input_mint, output_mint, amount, slippage_bps):
    url = f"https://quote-api.jup.ag/v6/quote?inputMint={input_mint}&outputMint={output_mint}&amount={amount}&slippageBps={slippage_bps}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
        return None
    except Exception as e:
        print(f"Jupiter quote error: {e}")
        return None

# ========== Modified buy and sell for paper mode ==========

def buy_token(token_address, amount_sol=BUY_AMOUNT_SOL, slippage=SLIPPAGE_BPS):
    """Simulate buy token with SOL."""
    if PAPER_MODE:
        print(f"[PAPER MODE] Would BUY {amount_sol} lamports of {token_address}")
        entry_price = asyncio.run(fetch_dexscreener_price(token_address))
        return 1000, entry_price  # Fake bought amount
    else:
        # Real trade code (not used in paper mode)
        return None, None

def sell_token(token_address, amount_token, slippage=SLIPPAGE_BPS):
    """Simulate sell token for SOL."""
    if PAPER_MODE:
        print(f"[PAPER MODE] Would SELL {amount_token} of {token_address}")
        return True
    else:
        return False

# ========== End of modified buy/sell ==========

async def monitor_position(token_address, entry_price, bought_amount):
    position_active = True
    tp_triggered = False
    peak_price = entry_price
    moonbag_amount = 0

    while position_active:
        current_price = await fetch_dexscreener_price(token_address)
        if current_price is None:
            time.sleep(60)
            continue

        gain = current_price / entry_price if entry_price > 0 else 0

        if not tp_triggered and gain >= 2:
            sell_amount = bought_amount * 0.5
            if sell_token(token_address, int(sell_amount)):
                tp_triggered = True
                moonbag_amount = bought_amount * 0.5
                peak_price = current_price
                print(f"TP hit at 2x. Sold 50%. Moonbag: {moonbag_amount}")

        if tp_triggered:
            if current_price > peak_price:
                peak_price = current_price
            if current_price < peak_price * 0.7:
                if sell_token(token_address, int(moonbag_amount)):
                    print(f"Trailing stop hit. Sold moonbag at {current_price}")
                    position_active = False

        time.sleep(60)

def main():
    pump_data = fetch_pump_fun_data()
    meteora_data = fetch_meteora_data()
    bonk_data = fetch_letsbonk_data()
    
    all_coins = pump_data + meteora_data + bonk_data
    df = pd.DataFrame(all_coins).fillna(0)
    
    token_addresses = {'ExampleCoin1': 'TokenMintAddress1SoL...abc'}
    twitter_handles = {'ExampleCoin1': 'examplehandle'}
    
    loop = asyncio.get_event_loop()
    for i, row in df.iterrows():
        token_addr = token_addresses.get(row['name'], 'N/A')
        df.at[i, 'token_address'] = token_addr
        
        if token_addr != 'N/A':
            df.at[i, 'contract_score'] = fetch_solsniffer_score(token_addr)
            df.at[i, 'fake_volume_flag'] = detect_fake_volume(token_addr)
            df.at[i, 'rugger_flag'] = check_rugger_deployer(token_addr)
        else:
            df.at[i, 'contract_score'] = 0
            df.at[i, 'fake_volume_flag'] = False
            df.at[i, 'rugger_flag'] = False
        
        price = loop.run_until_complete(fetch_dexscreener_price(token_addr)) if token_addr != 'N/A' else 0
        df.at[i, 'price'] = price
        df.at[i, 'price_change_1h'] = np.random.uniform(-5, 10)
        df.at[i, 'price_change_24h'] = np.random.uniform(-20, 50)
        solana_info = enrich_with_solana_data(row)
        df.at[i, 'supply'] = solana_info['supply']
        
        handle = twitter_handles.get(row['name'], None)
        if handle:
            twitter_data = evaluate_twitter(handle)
            df.at[i, 'twitter_handle'] = handle
            df.at[i, 'notable_followers_count'] = twitter_data['notable_followers_count']
            df.at[i, 'notable_followers_list'] = ', '.join(map(str, twitter_data['notable_followers_list']))
            df.at[i, 'trust_score'] = twitter_data['trust_score']
            df.at[i, 'reused_flag'] = twitter_data['reused_flag']
        else:
            df.at[i, 'twitter_handle'] = 'N/A'
            df.at[i, 'notable_followers_count'] = 0
            df.at[i, 'notable_followers_list'] = ''
            df.at[i, 'trust_score'] = 0
            df.at[i, 'reused_flag'] = False
    
    valid_df = df[
        (df['contract_score'] >= 85) &
        (~df['fake_volume_flag']) &
        (~df['rugger_flag'])
    ].copy()
    
    if valid_df.empty:
        print("No valid coins found after filtering.")
        return
    
    analyzed_df = analyze_profitability(valid_df)
    
    print("Top 5 Most Profitable Coins on Solana (after filtering):")
    print(analyzed_df.head(5)[['name', 'source', 'market_cap', 'volume', 'profitability_score']])
    
    top_coin = analyzed_df.iloc[0]
    token_addr = top_coin['token_address']
    if token_addr == 'N/A':
        print("No valid token address for top coin.")
        return
    
    bought_amount, entry_price = buy_token(token_addr)
    if bought_amount and entry_price:
        asyncio.run(monitor_position(token_addr, entry_price, bought_amount))
    else:
        print("Skipping buy for top coin.")

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f"Main loop error: {e}")
        time.sleep(3600)
