import requests


def fetch_sonic_token_data(token_symbol: str):
    """
    Fetches token data from DexScreener API for the Sonic network.

    :param token_symbol: The ticker symbol of the token (e.g., "SOLV", "WETH").
    :return: Dictionary with token details (price, liquidity, market cap, etc.).
    """
    url = f"https://api.dexscreener.com/latest/dex/search?q={token_symbol}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()

        if "pairs" in data and len(data["pairs"]) > 0:
            for pair in data["pairs"]:
                if pair.get("chainId") == "sonic":
                    return {
                        "token_name": pair["baseToken"]["name"],
                        "token_symbol": pair["baseToken"]["symbol"],
                        "price": pair["priceUsd"],
                        "liquidity": pair.get("liquidity", {}).get("usd", "NA"),
                        "market_cap": pair.get("fdv", "NA"),
                        "pair_url": pair["url"],
                        "volume_24h": pair.get("volume", {}).get("h24", "NA")
                    }

        return {"error": "Token not found on Sonic network"}

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# Example Usage:
token_data = fetch_sonic_token_data("SOLVBTC")
print(token_data)
