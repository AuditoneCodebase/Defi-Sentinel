from core.fetch_audits_hacks import get_audit_security_score, fetch_hacks_from_database
from core.fetch_tvl import get_symbol_metrics
import json

# Define projects with names mapped to their symbols
projects = {
    "Solv Protocol":"SOLVBTC",
    "Hey Anon":"ANON",
    "Wagmi":"WAGMI",
    "Yel Finance":"YEL",
    "Silo Finance":"SILO",
    "Beets":"BEETS",
    "Shadow":"SHADOW",
    "Eggs Finance": "EGGS",
    "Equalizer Exchange":"EQUAL"
}

def fetch_complete_data():
    """
    Fetches audit/security scores, past hack records, and TVL metrics for each project.

    :return: JSON containing all combined metrics.
    """
    combined_data = {}

    for project_name, symbol in projects.items():
        # Fetch audit/security score
        audit_security_score = get_audit_security_score(project_name)

        # Fetch hack history
        hack_data = fetch_hacks_from_database(project_name)

        # Fetch TVL & DeFi-related metrics
        symbol_metrics_json = get_symbol_metrics(symbol)
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

        # Combine all data
        combined_data[project_name] = {
            "auditSecurityScore": audit_security_score if audit_security_score else "NA",
            "pastHacks": hack_data if hack_data else "NA",
            "symbol": symbol,
            "tvlMetrics": symbol_metrics
        }

    return json.dumps(combined_data, indent=4)