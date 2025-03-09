import json
import requests

def analyze_defi_project(data):
    """
    Analyzes a DeFi project based on input data and requests a security and risk assessment.
    """

    # Extract data from input
    audit_security = data.get("auditSecurityScore", {})
    past_hacks = data.get("pastHacks", {})
    token_stats = data.get("tokenStats", {})

    # Construct the prompt dynamically
    prompt = f"""
    Analyze the following DeFi project and provide a security and risk assessment:

    **Project Name:** {audit_security.get("project_name", "Unknown")}
    **Audit Security Score:** {audit_security.get("total_score", "Not Available")}
    **Total Audits Conducted:** {audit_security.get("total_audits", "Unknown")}
    **Audited By:** {", ".join(audit_security.get("audited_by", [])) if audit_security.get("audited_by") else "None"}

    **Past Hacks Analysis:**
    - SlowMist Report: {past_hacks.get("slowmist", {}).get("message", "No data available")}
    - Rekt News Report: {past_hacks.get("rekt_news", {}).get("message", "No data available")}

    **Token Statistics:**
    - Token Symbol: {token_stats.get("token", "Unknown")}
    - Price (USD): ${token_stats.get("price_usd", "Unknown")}
    - 24h Trading Volume: ${token_stats.get("total_volume_24h", "Unknown")}
    - Liquidity Ratio: {token_stats.get("liquidity_ratio", "Unknown")}
    - Liquidity Risk: {token_stats.get("liquidity_risk", "Unknown")}
    - Buy/Sell Ratio: {token_stats.get("buy_sell_ratio", "Unknown")}
    - Market Sentiment: {token_stats.get("market_sentiment", "Unknown")}

    Provide an expert-level risk analysis for users interacting with this protocol, including security insights, investment risks, and any potential red flags.
    """

    # System prompt to guide the AI response
    system_prompt = "You are a DeFi security expert providing risk analysis for blockchain projects."

    # Model selection
    model = "gpt-4o"

    # API Request Payload
    payload = {
        "connection": "openai",
        "action": "generate-text",
        "params": [prompt, system_prompt, model]
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    url = "https://zerepy.auditone.io/agent/action"

    try:
        # Send API request
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()

        if response.status_code == 200:
            return response_data
        else:
            return {"error": f"API request failed with status {response.status_code}", "details": response_data}
    except Exception as e:
        return {"error": "Request failed", "details": str(e)}

