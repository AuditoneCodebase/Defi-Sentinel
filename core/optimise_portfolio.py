import copy
import requests

ZEREPY_API_URL = "https://zerepy.auditone.io/agent/action"

def rebalance_portfolio(tokens, target_security_score, private_key, top_n=1):
    """
    Adjusts token holdings to achieve a target weighted security score and executes swaps.

    :param tokens: List of tokens with security scores and holdings percentage.
    :param target_security_score: Desired weighted security score.
    :param private_key: User's private key for executing swaps.
    :param top_n: Number of top security tokens to rebalance into.
    :return: Updated token allocation for swap recommendations.
    """

    # Deep copy the tokens list to avoid modifying the input list
    tokens = copy.deepcopy(tokens)

    # Compute current weighted security score
    current_weighted_score = sum(
        (token["holding_percent"] / 100) * token["auditSecurityScore"]["total_score"]
        for token in tokens
    )

    if current_weighted_score >= target_security_score:
        return {"status": "error", "result": "Portfolio already meets or exceeds target security score. No rebalancing needed."}

    # Sort tokens by security score (low to high)
    tokens_sorted = sorted(tokens, key=lambda x: x["auditSecurityScore"]["total_score"])

    # Identify tokens to swap out (those with the lowest security scores)
    swap_tokens = []
    swap_out_holdings = 0
    for token in tokens_sorted:
        if token["auditSecurityScore"]["total_score"] < target_security_score:
            swap_tokens.append(token)
            swap_out_holdings += token["holding_percent"]
            token["holding_percent"] = 0  # Remove these from holdings

    if swap_out_holdings == 0:
        return {"status": "error", "result": "No low-security tokens found to swap out."}

    # Identify top N high-security tokens to reallocate into
    high_security_tokens = sorted(tokens, key=lambda x: x["auditSecurityScore"]["total_score"], reverse=True)[:top_n]

    if not high_security_tokens:
        return {"status": "error", "result": "No high-security tokens available for rebalancing."}

    # Compute total security score of the selected high-security tokens
    total_high_security_score = sum(t["auditSecurityScore"]["total_score"] for t in high_security_tokens)

    if total_high_security_score == 0:
        return {"status": "error", "result": "Total security score of selected tokens is zero. Cannot rebalance."}

    # Perform swaps for each swap-out token
    for swap_token in swap_tokens:
        # Select a high-security token to swap into
        target_token = high_security_tokens[0]  # Example: Swap into the first high-security token

        swap_amount = swap_token["balance"]
        token_from = swap_token["contract_address"]
        token_to = target_token["contract_address"]

        # Call the Zerepy API for swap execution
        payload = {
            "connection": "sonic",
            "action": "swap",
            "params": [private_key, token_from, token_to, str(swap_amount)]
        }

        response = requests.post(ZEREPY_API_URL, json=payload, headers={"accept": "application/json", "Content-Type": "application/json"})

        if response.status_code != 200:
            return {"status": "error", "result": f"Swap failed for {swap_token['symbol']} → {target_token['symbol']}"}

    # Redistribute the swapped holdings proportionally
    for token in high_security_tokens:
        weight = token["auditSecurityScore"]["total_score"] / total_high_security_score
        token["holding_percent"] += swap_out_holdings * weight  # Adjust holdings %

    return tokens
