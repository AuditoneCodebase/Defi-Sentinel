import requests


def load_agent():
    """Ensures the agent is loaded before fetching token stats."""
    url = "https://zerepy.auditone.io/agents/auditone-sonic/load"
    headers = {
        "accept": "application/json"
    }

    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        return True  # Agent loaded successfully
    else:
        print(f"Error loading agent: {response.status_code}")
        return False  # Failed to load agent

def stats_by_symbol(symbol):
    """Fetches token stats after ensuring the agent is loaded."""
    if not load_agent():
        return {"error": "Failed to load agent", "default_used": True}

    url = "https://zerepy.auditone.io/agent/action"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {
        "connection": "sonic",
        "action": "get-token-stats",
        "params": [symbol]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()

        # If API returns an error, use default values
        if result.get("status") == "error":
            result = {"status": "error", "result": {}}
    else:
        return {
            "token": symbol,
            "error": f"Failed to fetch stats, status code: {response.status_code}",
            "default_used": True
        }

    token_data = result.get("result", {})

    # Extract relevant values or default to "N/A"
    total_liquidity = token_data.get("totalLiquidityUsd", "N/A")
    total_market_cap = token_data.get("totalMarketCap", "N/A")
    total_buys = token_data.get("totalBuys", "N/A")
    total_sells = token_data.get("totalSells", "N/A")
    price_usd = token_data.get("priceUsd", "N/A")
    total_volume_24h = token_data.get("totalVolume24h", "N/A")

    # Calculate Liquidity Risk
    if isinstance(total_liquidity, (int, float)) and isinstance(total_market_cap,
                                                                (int, float)) and total_market_cap > 0:
        liquidity_risk = total_liquidity / total_market_cap
    else:
        liquidity_risk = "N/A"

    # Determine Liquidity Risk Level
    if isinstance(liquidity_risk, float):
        if liquidity_risk < 0.001:
            liquidity_risk_level = "High"
        elif 0.001 <= liquidity_risk < 0.01:
            liquidity_risk_level = "Medium"
        else:
            liquidity_risk_level = "Low"
    else:
        liquidity_risk_level = "N/A"

    # Calculate Buy-Sell Ratio
    if isinstance(total_buys, (int, float)) and isinstance(total_sells, (int, float)) and total_sells > 0:
        buy_sell_ratio = total_buys / total_sells
    else:
        buy_sell_ratio = "N/A"

    # Determine Market Sentiment
    if isinstance(buy_sell_ratio, float):
        market_sentiment = "Bearish" if buy_sell_ratio < 1 else "Bullish"
    else:
        market_sentiment = "N/A"

    # Construct Final JSON Output
    return {
        "token": token_data.get("token", symbol),
        "price_usd": price_usd,
        "total_volume_24h": total_volume_24h,
        "liquidity_ratio": round(liquidity_risk,2),
        "liquidity_risk": liquidity_risk_level,
        "buy_sell_ratio": round(buy_sell_ratio,2),
        "market_sentiment": market_sentiment
    }
