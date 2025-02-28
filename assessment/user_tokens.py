import json
import os
import requests
from dotenv import load_dotenv

# Import functions from your files
from core.fetch_user_tokens import get_tokens_held
from core.fetch_audits_hacks import get_audit_security_score, fetch_hacks_from_database
from core.fetch_tvl import get_symbol_metrics

# Load API Key for CoinMarketCap from environment
load_dotenv()
CMC_API_KEY = os.getenv("CMC_API")

# Function to fetch token price from CoinMarketCap API
def get_token_price_from_cmc(token_symbol):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {
        'X-CMC_PRO_API_KEY': CMC_API_KEY,
        'Accept': 'application/json',
    }
    params = {
        'symbol': token_symbol,
        'convert': 'USD'
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('status').get('error_code') == 0:
                price = data['data'][token_symbol.upper()]['quote']['USD']['price']
                return price
    except:
        return 0


# Fetch user token data, USD price and TVL metrics for the user's tokens
def fetch_user_and_project_data(chain, wallet_address, api_key):
    combined_data = {}

    # Fetch user tokens using the function from `fetch_user_tokens.py`
    user_tokens = get_tokens_held(chain, wallet_address, api_key)
    if "error" in user_tokens:
        return json.dumps({"error": "Failed to fetch user token data", "details": user_tokens}, indent=4)

    # Iterate over each token the user holds
    for token in user_tokens:
        token_symbol = token['symbol']
        token_name = token['name']
        token_balance = token['balance']

        # Fetch audit/security score and hack history
        audit_security_score = get_audit_security_score(token_name)
        hack_data = fetch_hacks_from_database(token_name)

        # Fetch TVL & DeFi-related metrics
        symbol_metrics_json = get_symbol_metrics(token_symbol)
        symbol_metrics = json.loads(symbol_metrics_json)

        # Handle missing symbol metrics
        if "error" in symbol_metrics:
            symbol_metrics = {
                "totalTvl": "NA",
                "avgApy": "NA",
                "avgSigma": "NA",
                "impermanentLossRisk": "NA",
                "predictedProbability": "NA",
                "totalVolume1d": "NA",
                "totalVolume7d": "NA",
                "numPools": "NA"
            }

        # Get USD price for the token
        usd_price = get_token_price_from_cmc(token_symbol)

        # Combine all token data
        combined_data[token_symbol] = {
            "tokenName": token_name,
            "tokenSymbol": token_symbol,
            "balance": token_balance,
            "usdPrice": usd_price if usd_price else "NA",
            "auditSecurityScore": audit_security_score if audit_security_score else "NA",
            "pastHacks": hack_data if hack_data else "NA",
            "tvlMetrics": symbol_metrics
        }

    return json.dumps(combined_data, indent=4)

