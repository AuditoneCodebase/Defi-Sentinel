import requests
import os
from dotenv import load_dotenv

load_dotenv()

CMC_API_KEY = os.getenv("CMC_API")
CMC_QUOTE_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
CMC_INFO_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/info"


def safe_get(data, key):
    """Safely fetch a key from a dictionary, handling empty lists and missing keys."""
    value = data.get(key, [])
    if isinstance(value, list) and value:  # Check if it's a non-empty list
        return value[0]
    if isinstance(value, str):  # If it's already a string, return it
        return value
    return "N/A"  # Default return for missing or empty values


def fetch_single_token_data(symbol):
    """
    Fetches details for a single token from CoinMarketCap.
    :param symbol: Token symbol (e.g., 'ETH', 'BTC')
    :return: Dictionary with token details
    """
    if not CMC_API_KEY:
        return {"error": "Missing CoinMarketCap API key"}

    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": CMC_API_KEY,
    }

    # Fetch project details
    try:
        info_response = requests.get(CMC_INFO_URL, headers=headers, params={"symbol": symbol})
        info_data = info_response.json()
        if "data" not in info_data:
            return {"error": "Invalid response from CoinMarketCap Info API"}
    except Exception as e:
        return {"error": f"Failed to fetch CoinMarketCap project info: {e}"}

    # Fetch price in USD
    try:
        quote_response = requests.get(CMC_QUOTE_URL, headers=headers, params={"symbol": symbol})
        quote_data = quote_response.json()
        if "data" not in quote_data:
            return {"error": "Invalid response from CoinMarketCap Quote API"}
    except Exception as e:
        return {"error": f"Failed to fetch CoinMarketCap price data: {e}"}

    token_data = {}

    if symbol in quote_data["data"]:
        token_data["price_usd"] = quote_data["data"][symbol]["quote"]["USD"]["price"]

    if symbol in info_data["data"]:
        crypto_data = info_data["data"][symbol]
        token_data.update({
            "name": crypto_data.get("name"),
            "symbol": crypto_data.get("symbol"),
            "category": crypto_data.get("category"),
            "description": crypto_data.get("description", "No description available"),
            "website": safe_get(crypto_data["urls"], "website"),
            "dateAdded": crypto_data.get("date_added"),
            "dateLaunched": crypto_data.get("date_launched"),
            "infiniteSupply": crypto_data.get("infinite_supply", False),
            "technical": {
                "documentation": {
                    "whitepaper": safe_get(crypto_data["urls"], "technical_doc"),
                    "sourceCode": safe_get(crypto_data["urls"], "source_code"),
                },
                "explorers": crypto_data["urls"].get("explorer", [])
            },
            "social": {
                "twitter": safe_get(crypto_data["urls"], "twitter"),
                "reddit": safe_get(crypto_data["urls"], "reddit"),
                "forum": safe_get(crypto_data["urls"], "message_board"),
                "chatGroups": {
                    "discord": safe_get(crypto_data["urls"], "chat"),
                    "telegram": safe_get(crypto_data["urls"], "chat") if len(
                        crypto_data["urls"].get("chat", [])) > 1 else "N/A"
                },
                "announcement": safe_get(crypto_data["urls"], "announcement")
            }
        })

    return token_data

