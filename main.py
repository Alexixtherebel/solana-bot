import time
from datetime import datetime, timezone
# (keep all your previous imports here)

# ===== NEW FLAGS =====
PAPER_TRADE = True  # Change to False after 1 week

SCAN_INTERVAL = 600  # 10 minutes (was 3600)

MIN_TOKEN_AGE_MINUTES = 60  # Token must be at least 1 hour old


# ======= (all your existing code remains the same above) =======

def get_token_age_minutes(token_address):
    """Estimate token age by checking first transaction signature timestamp."""
    try:
        signatures = SOLANA_CLIENT.get_signatures_for_address(Pubkey.from_string(token_address), limit=1).value
        if not signatures:
            return 9999
        first_sig = signatures[0]
        block_time = first_sig.block_time
        if block_time:
            created_at = datetime.fromtimestamp(block_time, tz=timezone.utc)
            return (datetime.now(timezone.utc) - created_at).total_seconds() / 60
    except Exception as e:
        print(f"Token age check error: {e}")
    return 9999


def main():
    # Collect data
    pump_data = fetch_pump_fun_data()
    meteora_data = fetch_meteora_data()
    bonk_data = fetch_letsbonk_data()
    
    all_coins = pump_data + meteora_data + bonk_data
    df = pd.DataFrame(all_coins).fillna(0)
    
    # Placeholder mappings (expand with real data)
    token_addresses = {
        'ExampleCoin1': 'TokenMintAddress1SoL...abc',
    }
    twitter_handles = {
        'ExampleCoin1': 'examplehandle',
    }
    
    loop = asyncio.get_event_loop()
    for i, row in df.iterrows():
        token_addr = token_addresses.get(row['name'], 'N/A')
        df.at[i, 'token_address'] = token_addr

        # ======== NEW FILTER: TOKEN AGE ========
        if token_addr != 'N/A':
            age_minutes = get_token_age_minutes(token_addr)
            if age_minutes < MIN_TOKEN_AGE_MINUTES:
                print(f"Skipping {row['name']} ({token_addr}): Token too new ({age_minutes:.1f} mins old).")
                df.at[i, 'rugger_flag'] = True
                continue

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

    # ======= PAPER TRADE LOGIC ========
    if PAPER_TRADE:
        print(f"[PAPER] Would BUY {token_addr} with {BUY_AMOUNT_SOL} lamports")
        # simulate monitoring
        print(f"[PAPER] Would monitor and sell when TP/trailing stop is hit.")
    else:
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
        time.sleep(SCAN_INTERVAL)
