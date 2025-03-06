from core.fetch_audit_stats import audit_data
from core.fetch_past_hacks import hacks_data
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
            "market_sentiment": "NA"
        }

    # Combine all data
    project_data = {
        "auditSecurityScore": audit_security_score if audit_security_score else 0,
        "pastHacks": hack_data if hack_data else "NA",
        "symbol": symbol,
        "tokenStats": token_stats
    }

    return project_data
