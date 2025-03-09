from utils.db_client import client
import json

db = client["agentDatabase"]
collection = db["tvlSonicProjects"]

def get_symbol_metrics(symbol):
    """
    Fetches all available metrics for a given symbol from MongoDB.

    :param symbol: The symbol of the token to assess.
    :return: JSON containing all combined metrics for the given symbol.
    """
    filtered_pools = list(collection.find({
        "symbol": {
            "$regex": symbol,  # Substring to search for
            "$options": "i"  # "i" = case-insensitive
        }
    }))

    if not filtered_pools:
        return json.dumps({"error": f"No data found for symbol {symbol}"}, indent=4)

    # Initialize metrics
    total_tvl = 0
    total_apy = 0
    total_sigma = 0
    total_il_risk = 0
    total_prediction_prob = 0
    total_volume_1d = 0
    total_volume_7d = 0
    count = len(filtered_pools)

    for pool in filtered_pools:
        total_tvl += pool.get("tvlUsd", 0)
        apy_base = pool.get("apyBase")
        if apy_base is None:
            apy_base = 0
        total_apy += apy_base

        total_sigma += pool.get("sigma", 0)
        total_il_risk += 1 if pool.get("ilRisk", "no") == "yes" else 0
        total_volume_1d += pool.get("volumeUsd1d", 0) or 0
        total_volume_7d += pool.get("volumeUsd7d", 0) or 0

        # Handle missing values
        prediction_prob = pool.get("predictions", {}).get("predictedProbability", 50)
        total_prediction_prob += prediction_prob if prediction_prob is not None else 50  # Default to 50%

    # Compute averages
    avg_apy = total_apy / count
    avg_sigma = total_sigma / count
    avg_prediction_prob = total_prediction_prob / count
    avg_il_risk = total_il_risk / count  # Percentage of pools with IL risk

    # Construct output JSON
    output = {
        "symbol": symbol,
        "totalTvl": total_tvl,
        "avgApy": round(avg_apy, 2),
        "avgSigma": round(avg_sigma, 4),
        "impermanentLossRisk": round(avg_il_risk, 2),  # % of pools with IL risk
        "predictedProbability": round(avg_prediction_prob, 2),
        "totalVolume1d": total_volume_1d,
        "totalVolume7d": total_volume_7d,
        "numPools": count
    }

    return json.dumps(output, indent=4)
