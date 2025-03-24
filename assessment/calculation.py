from core.fetch_token_stats import stats_by_symbol
from core.fetch_security_stats import stats_by_project
import json
def dashboard_stats(project_name,symbol):
    """
    Fetches audit/security score, past hack records, and token metrics for a given project.

    :param project_name: The name of the project.
    :return: JSON containing all combined metrics for the specified project.
    """
    # Fetch audit/security score
    security_stats = stats_by_project(project_name)
    audit_security_score = security_stats["audit_data"]

    # Fetch hack history
    hack_data = security_stats["hacks_data"]

    new_security_incident = 0

    # Check if hack_data is a dictionary and contains the required keys
    if isinstance(hack_data, dict) and "slowmist" in hack_data and "rekt_news" in hack_data:
        slowmist_data = hack_data["slowmist"]
        rekt_news_data = hack_data["rekt_news"]

        # Function to check if "No hacks found" is present
        def no_hacks_found(data):
            if isinstance(data, dict):
                return data.get("message", "").lower() == "no hacks found"
            elif isinstance(data, list):
                return all(
                    isinstance(item, dict) and item.get("message", "").lower() == "no hacks found" for item in data)
            return False

        if no_hacks_found(slowmist_data) and no_hacks_found(rekt_news_data):
            new_security_incident = 100

    # Fetch token stats
    token_stats = stats_by_symbol(symbol)

    # Handle missing token stats
    if "error" in token_stats:
        token_stats = {
            "price_usd": "NA",
            "total_volume_24h": "NA",
            "liquidity_ratio": "NA",
            "liquidity_risk": "NA",
            "buy_sell_ratio": "NA",
            "market_sentiment": "NA",
            "total_market_cap":"NA"
        }

    market_sentiment = token_stats.get("market_sentiment", 1)

    if market_sentiment == "Bullish":
        market_sentiment_score = 100  # Bullish
    elif market_sentiment == "Neutral":
        market_sentiment_score = 50  # Neutral
    else:
        market_sentiment_score = 0  # Bearish

    # Fetch liquidity risk
    liquidity_risk = token_stats.get("liquidity_risk", 0)

    if liquidity_risk == "Low":
        liquidity_score = 100
    elif liquidity_risk == "Medium":
        liquidity_score = 50
    else:
        liquidity_score = 0

    # Compute Health Score
    health_score = (
            (0.3 * audit_security_score["total_score"]) +
            (0.3 * market_sentiment_score) +
            (0.2 * liquidity_score) +
            (0.2 * new_security_incident)
    )

    # Combine all data
    project_data = {
        "auditSecurityScore": audit_security_score if audit_security_score else 0,
        "pastHacks": hack_data if hack_data else "NA",
        "symbol": symbol,
        "tokenStats": token_stats,
        "healthScore":health_score
    }

    return project_data