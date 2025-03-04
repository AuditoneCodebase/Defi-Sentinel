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
    params = {
        'symbol': token_symbol,
        'convert': 'USD'
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('status', {}).get('error_code') == 0:
                price = data['data'][token_symbol.upper()]['quote']['USD']['price']
                return round(price, 4)  # Keep a bit more precision here before final rounding
    except:
        pass
    return 0

def compute_raw_risk(security_score, impermanent_loss):
    """
    Example formula for raw risk:
      raw_risk = (100 - security_score) + impermanent_loss
    If either is 'NA', treat it as 0.
    """
    if security_score == "NA" or security_score is None:
        sec_score = 0
    else:
        sec_score = float(security_score)

    if impermanent_loss == "NA":
        il_value = 0
    else:
        il_value = float(impermanent_loss)

    # Higher security score => lower base risk
    base_risk = 100 - sec_score

    return base_risk + il_value

def hacks_reported(hack_data):
    """
    Returns "Yes" if hack_data indicates any hacks found, else "No".
    """
    if hack_data == "NA" or not isinstance(hack_data, dict):
        return "No"

    slowmist_msg = hack_data.get("slowmist", {}).get("message", "")
    rekt_msg = hack_data.get("rekt_news", {}).get("message", "")

    # If either message is not "No hacks found", then "Yes"
    if slowmist_msg != "No hacks found" or rekt_msg != "No hacks found":
        return "Yes"
    return "No"


def fetch_user_and_project_data(chain, wallet_address, api_key):
    """
    Fetch all tokens for a user, plus TVL metrics, security score, etc.
    Then compute Weighted Risk based on the fraction of the portfolio
    each token represents in USD.
    """

    # Fetch the user's token holdings
    user_tokens = get_tokens_held(chain, wallet_address, api_key)
    if "error" in user_tokens:
        return json.dumps({
            "error": "Failed to fetch user token data",
            "details": user_tokens
        }, indent=4)

    # 1) First pass: gather raw data
    token_data_list = []  # Temporary list to store info before computing fractions

    for token in user_tokens:
        token_symbol = token["symbol"]
        token_name = token["name"]
        token_balance = round(token["balance"], 4)

        # Security score
        audit_security_score = get_audit_security_score(token_name)
        if audit_security_score and "total_score" in audit_security_score:
            security_score = audit_security_score["total_score"]
        else:
            security_score = "NA"

        # Past hacks
        hack_data = fetch_hacks_from_database(token_name)
        hack_flag = hacks_reported(hack_data)  # "Yes" or "No"

        # TVL metrics
        tvl_json = get_symbol_metrics(token_symbol)
        tvl_data = json.loads(tvl_json)
        if "error" in tvl_data:
            tvl_data = {
                "totalTvl": "NA",
                "avgApy": "NA",
                "impermanentLossRisk": "NA",
                "numPools": "NA"
            }

        # Price
        usd_price = get_token_price_from_cmc(token_symbol)
        final_price = usd_price if usd_price != 0 else 0  # store zero if not found

        # USD value = balance * price
        usd_value = round(token_balance * final_price, 2)

        # Compute raw_risk using your formula
        raw_risk = compute_raw_risk(
            security_score,
            tvl_data.get("impermanentLossRisk", "NA")
        )

        token_data_list.append({
            "symbol": token_symbol,
            "name": token_name,
            "balance": token_balance,
            "usdPrice": final_price if final_price else "NA",
            "usdValue": usd_value,  # for weighting
            "securityScore": security_score,
            "hackFlag": hack_flag,
            "tvlMetrics": {
                "totalTvl": tvl_data.get("totalTvl", "NA"),
                "avgApy": tvl_data.get("avgApy", "NA"),
                "impermanentLossRisk": tvl_data.get("impermanentLossRisk", "NA"),
                "numPools": tvl_data.get("numPools", "NA")
            },
            "rawRisk": raw_risk
        })

    # 2) Calculate total portfolio USD
    total_portfolio_usd = sum(t["usdValue"] for t in token_data_list)

    # 3) Second pass: compute fraction and weighted risk for each token
    #    fraction_of_portfolio = (token_usd_value / total_portfolio_usd)
    #    weighted_risk = raw_risk * fraction_of_portfolio
    #    Round to 2 decimals.

    combined_data = {}
    for t in token_data_list:
        # If total_portfolio_usd = 0, avoid division by zero
        if total_portfolio_usd > 0:
            fraction = t["usdValue"] / total_portfolio_usd
        else:
            fraction = 0

        # Weighted Risk
        weighted_risk = round(t["rawRisk"] * fraction, 2)

        combined_data[t["symbol"]] = {
            "tokenName": t["name"],
            "tokenSymbol": t["symbol"],
            "balance": t["balance"],
            "usdPrice": t["usdPrice"] if t["usdPrice"] != 0 else "NA",
            "usdValue": t["usdValue"],  # how much USD the user holds
            "percentOfPortfolio": f"{round(fraction*100, 2)}%",  # e.g. 23.45%
            "auditSecurityScore": {
                "total_score": t["securityScore"]
            },
            "risk": {
                "rawRisk": round(t["rawRisk"], 2),
                "weightedRisk": weighted_risk
            },
            "pastHacks": t["hackFlag"],  # "Yes" or "No"
            "tvlMetrics": t["tvlMetrics"]
        }

    return json.dumps(combined_data, indent=4)


#print(fetch_user_and_project_data("sonic","0x79bbF4508B1391af3A0F4B30bb5FC4aa9ab0E07C",os.getenv("SONIC_API_KEY")))
