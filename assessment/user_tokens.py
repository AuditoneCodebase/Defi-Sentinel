import json
import os
import requests
from dotenv import load_dotenv

# Import functions from your files
from core.fetch_user_tokens import get_tokens_held
from core.fetch_audits_hacks import get_audit_security_score, fetch_hacks_from_database
from core.fetch_tvl import get_symbol_metrics

load_dotenv()
CMC_API_KEY = os.getenv("CMC_API")


def get_token_price_from_cmc(token_symbol):
    """
    Fetch token price (USD) from CoinMarketCap API.
    Returns a float or 0 on error.
    """
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {
        'X-CMC_PRO_API_KEY': CMC_API_KEY,
        'Accept': 'application/json',
    }
    params = {'symbol': token_symbol, 'convert': 'USD'}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('status', {}).get('error_code') == 0:
                return round(data['data'][token_symbol.upper()]['quote']['USD']['price'], 4)
    except:
        pass
    return 0


def hacks_reported(hack_data):
    """
    Returns "Yes" if hack_data indicates any hacks found, else "No".
    """
    if hack_data == "NA" or not isinstance(hack_data, dict):
        return "No"
    return "Yes" if any(
        hack_data.get(source, {}).get("message", "") != "No hacks found"
        for source in ["slowmist", "rekt_news"]
    ) else "No"


def fetch_user_and_project_data(chain, wallet_address, api_key):
    """
    Fetch all tokens for a user, plus TVL metrics, security score, etc.
    Then compute Weighted Risk based on the fraction of the portfolio
    each token represents in USD.
    """

    # Fetch the user's token holdings
    user_tokens = get_tokens_held(chain, wallet_address, api_key)
    if "error" in user_tokens:
        return json.dumps({"error": "Failed to fetch user token data", "details": user_tokens}, indent=4)

    token_data_list = []  # Temporary list to store raw data

    for token in user_tokens:
        token_symbol = token["symbol"]
        token_name = token["name"]
        token_balance = round(token["balance"], 4)

        # Security score
        audit_security_score = get_audit_security_score(token_name)
        security_score = audit_security_score.get("total_score", "NA") if audit_security_score else "NA"

        # Past hacks
        hack_data = fetch_hacks_from_database(token_name)
        hack_flag = hacks_reported(hack_data)  # "Yes" or "No"

        # TVL metrics
        tvl_json = get_symbol_metrics(token_symbol)
        tvl_data = json.loads(tvl_json) if "error" not in tvl_json else {}

        tvl_metrics = {
            "totalTvl": tvl_data.get("totalTvl", "NA"),
            "avgApy": tvl_data.get("avgApy", "NA"),
            "impermanentLossRisk": tvl_data.get("impermanentLossRisk", "NA"),
            "numPools": tvl_data.get("numPools", "NA"),
            "predictedProbability": tvl_data.get("predictedProbability", "NA")
        }

        # Price
        usd_price = get_token_price_from_cmc(token_symbol) or 0  # Ensure 0 if not found

        # USD value = balance * price
        usd_value = round(token_balance * usd_price, 2)

        # Use only predictedProbability as the risk value
        risk_value = float(tvl_metrics["predictedProbability"]) if tvl_metrics["predictedProbability"] not in ["NA",
                                                                                                               None] else 0

        token_data_list.append({
            "symbol": token_symbol,
            "name": token_name,
            "balance": token_balance,
            "usdPrice": usd_price if usd_price > 0 else "NA",
            "usdValue": usd_value,  # For weighting risk
            "securityScore": security_score,
            "hackFlag": hack_flag,
            "tvlMetrics": tvl_metrics,
            "riskValue": risk_value
        })

    # Calculate total portfolio USD value
    total_portfolio_usd = sum(t["usdValue"] for t in token_data_list)

    # Second pass: Compute percentOfPortfolio & weighted risk
    combined_data = {}
    for t in token_data_list:
        fraction = (t["usdValue"] / total_portfolio_usd) if total_portfolio_usd > 0 else 0
        weighted_risk = round(t["riskValue"] * fraction, 2)

        combined_data[t["symbol"]] = {
            "tokenName": t["name"],
            "tokenSymbol": t["symbol"],
            "balance": t["balance"],
            "usdPrice": t["usdPrice"] if t["usdPrice"] != 0 else "NA",
            "usdValue": t["usdValue"],  # USD holdings
            "percentOfPortfolio": round(fraction * 100, 2) if fraction > 0 else 0,  # Proper numeric value
            "auditSecurityScore": {"total_score": t["securityScore"]},
            "risk": {
                "rawRisk": round(t["riskValue"], 2),
                "weightedRisk": weighted_risk
            },
            "pastHacks": t["hackFlag"],  # "Yes" or "No"
            "tvlMetrics": t["tvlMetrics"]
        }

    return json.dumps(combined_data, indent=4)

