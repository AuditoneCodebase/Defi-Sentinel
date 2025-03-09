import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Mapping of supported chains and their corresponding explorers
CHAIN_API_BASE_URLS = {
    "sonic": "https://api.sonicscan.org/api"
}

# Blocklist of known spam token contracts (can be updated)
SPAM_TOKENS = [
    "0xspamtokencontract1...",
    "0xspamtokencontract2..."
]

# Minimum balance threshold to filter small airdrops (set to 0.01 as default)
MIN_BALANCE_THRESHOLD = 0.01

def get_tokens_held(chain, wallet_address, api_key):
    """
    Fetches only the actual ERC-20 tokens held by a wallet on Sonic,
    excluding transactions and ensuring accurate balances.

    :param chain: The blockchain to query ('sonic').
    :param wallet_address: The wallet address to check.
    :param api_key: The API key for the blockchain explorer.
    :return: A list of token balances the user actually holds.
    """
    if chain not in CHAIN_API_BASE_URLS:
        return {"error": "Unsupported chain"}

    api_url = f"{CHAIN_API_BASE_URLS[chain]}?module=account&action=tokentx&address={wallet_address}&sort=desc&apikey={api_key}"

    response = requests.get(api_url)

    if response.status_code != 200:
        return {"error": f"Failed to fetch data, HTTP Status: {response.status_code}"}

    data = response.json()

    if data.get("status") != "1":
        return {"error": data.get("message", "Unknown error")}

    tokens = {}

    for tx in data["result"]:
        sender = tx["from"].lower()
        receiver = tx["to"].lower()
        token_contract = tx["contractAddress"].lower()
        token_name = tx["tokenName"]
        token_symbol = tx["tokenSymbol"]
        value = int(tx["value"]) / (10 ** int(tx["tokenDecimal"]))

        # **Ignore spam tokens**
        if token_contract in SPAM_TOKENS:
            continue

        # **Initialize token if not already in dictionary**
        if token_contract not in tokens:
            tokens[token_contract] = {
                "name": token_name,
                "symbol": token_symbol,
                "contract_address": token_contract,
                "balance": 0
            }

        # **Add balance if received, subtract if sent**
        if receiver == wallet_address.lower():
            tokens[token_contract]["balance"] += value
        elif sender == wallet_address.lower():
            tokens[token_contract]["balance"] -= value

    # **Filter out tokens with zero or negative balance**
    filtered_tokens = [token for token in tokens.values() if token["balance"] > MIN_BALANCE_THRESHOLD]

    return filtered_tokens  # Return only tokens the user actually holds