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

# Minimum balance threshold to filter small airdrops (set to 1 as default)
MIN_BALANCE_THRESHOLD = 1

def get_tokens_held(chain, wallet_address, api_key):
    """
    Fetches ERC-20 tokens held by a wallet on a specified chain (Base or Sonic),
    excluding airdrops and transactions with `input: deprecated`, while aggregating balances.

    :param chain: The blockchain to query ('base' or 'sonic').
    :param wallet_address: The wallet address to check.
    :param api_key: The API key for the blockchain explorer.
    :return: A list of token balances.
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
        token_contract = tx["contractAddress"].lower()
        token_name = tx["tokenName"]
        token_symbol = tx["tokenSymbol"]
        value = int(tx["value"]) / (10 ** int(tx["tokenDecimal"]))

        # **Filter Conditions**
        if sender == "0x0000000000000000000000000000000000000000":  # Exclude minting from zero address
            continue
        if token_contract in SPAM_TOKENS:  # Exclude known spam tokens
            continue
        if value < MIN_BALANCE_THRESHOLD:  # Ignore tiny airdrops
            continue


        # **Aggregate token balances**
        if token_contract not in tokens:
            tokens[token_contract] = {
                "name": token_name,
                "symbol": token_symbol,
                "contract_address": token_contract,
                "balance": 0  # Initialize balance to 0
            }

        tokens[token_contract]["balance"] += value  # Add balance from multiple transactions

    return list(tokens.values())  # Convert dict to list of dicts
