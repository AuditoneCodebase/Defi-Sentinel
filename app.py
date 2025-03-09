import copy

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_session import Session
from utils.db_client import client
from web3 import Web3
import datetime
import uuid
import functools
from assessment.calculation import dashboard_stats
from core.fetch_user_tokens import get_tokens_held
from core.generate_report import analyze_defi_project
from core.optimise_portfolio import rebalance_portfolio
from assessment.agent_choice import project_list, project_for_dashboard
from openai import OpenAI
from dotenv import load_dotenv
import os
import markdown2
import urllib.parse
from eth_account import Account

import json

load_dotenv()

app = Flask(__name__)
CORS(app)

app.secret_key = os.getenv("SECRET_KEY")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
db = client["agentDatabase"]
users = db["users_sonic"]


SONIC_RPC_URL = "https://rpc.soniclabs.com"  # Replace with actual RPC URL
WEB3 = Web3(Web3.HTTPProvider(SONIC_RPC_URL))

# Required payment amount in native Sonic tokens
SONIC_NATIVE_TOKEN_COST = WEB3.to_wei(0.5, "ether")  # Example: 0.5 Sonic token required

# Payment recipient address (your address)
RECIPIENT_ADDRESS = "0x5A8eF3672fFAc8007ce2d025cebEbBAFb7F6e01B"  # Replace with your Sonic wallet address


# Register the custom markdown filter
@app.template_filter('markdown')
def markdown_filter(text):
    return markdown2.markdown(text)

# **Authentication Decorator**
def login_required(f):
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        if "wallet_address" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrap


# **Render the Frontend**
@app.route("/connect-wallet")
def index():
    return render_template("index.html")


# **Store Wallet Address in Session & Database**
@app.route("/store-wallet", methods=["POST"])
def store_wallet():
    data = request.json
    wallet_address = data.get("walletAddress")
    if not wallet_address:
        return jsonify({"error": "Wallet address required"})

    session["wallet_address"] = wallet_address
    user = users.find_one({"wallet_address": wallet_address})

    if user:
        users.update_one(
            {"wallet_address": wallet_address},
            {"$push": {"access_times": datetime.datetime.utcnow()}},
        )
    else:
        users.insert_one({
            "_id": str(uuid.uuid4().hex),
            "wallet_address": wallet_address,
            "created_at": datetime.datetime.utcnow(),
            "access_times": [datetime.datetime.utcnow()]
        })

    return jsonify({"message": "Wallet address stored", "redirect": "/my-tokens"})


@app.route("/")
#@login_required
def dashboard():
    protocols_data = []
    for name,symbol in project_for_dashboard.items():
        protocol_stats = dashboard_stats(name,symbol)
        protocols_data.append(protocol_stats)
    return render_template("dashboard.html",protocols=protocols_data)


@app.route("/get-report/<project_name>", methods=["GET"])
@login_required
def get_report(project_name):
    try:
       details = db.aiReports.find_one({"project":project_name})
       ai_report = details.get("aiReport","Could not fetch report for this project")
    except Exception as e:
        return jsonify({"error": f"Failed to generate report: {str(e)}"})
    return render_template("report.html", project_name=project_name, report=ai_report)


@app.route("/my-tokens")
@login_required
def my_tokens():
    """
    Fetches the user's tokens, retrieves their dashboard stats,
    and calculates the percentage of holdings in the portfolio.
    """
    user_tokens = get_tokens_held("sonic", session["wallet_address"], os.getenv("SONIC_API_KEY"))
    if not user_tokens or isinstance(user_tokens, dict):
        return render_template("my-tokens.html", message="No tokens found or an error occurred.")
    protocols_data = []
    total_portfolio_value = 0
    # Fetch all details from dashboard_stats in one loop
    for token in user_tokens:
        protocol_stats = dashboard_stats(token["name"], token["symbol"])
        # Extract price and calculate token's value in USD
        token_price = protocol_stats.get("tokenStats", {}).get("price_usd", 0)
        token_value = token["balance"] * token_price
        # Store processed data
        token["value_usd"] = round(token_value, 2)
        token["price_usd"] = round(token_price, 4)
        token["contract_address"] = token["contract_address"]
        total_portfolio_value += token_value  # Update total holdings value
        # Merge dashboard_stats data directly into token dictionary
        token.update(protocol_stats)
        protocols_data.append(token)
    # Calculate percentage holdings
    for token in protocols_data:
        if total_portfolio_value > 0:
            token["holding_percent"] = round((token["value_usd"] / total_portfolio_value) * 100, 2)
        else:
            token["holding_percent"] = 0
    return render_template("my-tokens.html", protocols=protocols_data, total_value=round(total_portfolio_value, 2))


@app.route("/analyze-token")
@login_required
def analyze_token():
    """
    Fetch tokens and display the analysis page.
    """
    if "wallet_address" not in session:
        return redirect(url_for("login"))
    combined_tokens = {name: symbol for name, symbol in project_list.items()}
    user_tokens = get_tokens_held("sonic", session["wallet_address"], os.getenv("SONIC_API_KEY"))
    # Ensure `user_tokens` is iterable
    if isinstance(user_tokens, list) and len(user_tokens) > 0:
        for token in user_tokens:
            combined_tokens[token["name"]] = token["symbol"]
    session["combined_tokens"] = combined_tokens
    reports = list(db.reports.find({"userId": session["wallet_address"]}, {"_id": 0}))
    return render_template("analyze-token.html", combined_tokens=combined_tokens, reports=reports)


def validate_payment(tx_hash):
    """
    Validate if the transaction meets payment requirements.
    """
    try:
        tx = WEB3.eth.get_transaction(tx_hash)
        receipt = WEB3.eth.get_transaction_receipt(tx_hash)
    except Exception:
        return {"status": "failed", "reason": "Transaction not found."}
    if not receipt or receipt["status"] != 1:
        return {"status": "failed", "reason": "Transaction failed or not confirmed."}
    if tx["to"].lower() != RECIPIENT_ADDRESS.lower():
        return {"status": "failed", "reason": "Transaction was sent to the wrong address."}
    if tx["value"] < SONIC_NATIVE_TOKEN_COST:
        return {"status": "failed", "reason": "Insufficient payment amount."}
    return {"status": "success", "sender": tx["from"], "tx_hash": tx_hash}


@app.route("/process-payment", methods=["POST"])
@login_required
def process_payment():
    """
    Handles payment verification.
    """
    data = request.json
    tx_hash = data.get("txHash")
    if not tx_hash:
        return jsonify({"error": "Transaction hash required"}), 400
    validation = validate_payment(tx_hash)
    if validation["status"] == "success":
        session["payment_verified"] = True
        return jsonify({"success": True, "message": "Payment verified!"})
    else:
        return jsonify({"error": validation["reason"]}), 400


@app.route("/generate-report/<name>", methods=["GET"])
@login_required
def generate_report(name):
    """
    Generates a risk analysis report only if payment is confirmed.
    """
    if not session.get("payment_verified"):
        return jsonify({"error": "Payment required before analysis."}), 403
    user_id = session.get("wallet_address", "unknown_user")
    combined_list = session["combined_tokens"]
    encoded_name = urllib.parse.unquote(name)
    data = dashboard_stats(encoded_name,combined_list[encoded_name])
    ai_report = analyze_defi_project(data)["result"]
    report_html = markdown2.markdown(ai_report)
    # Generate report data
    report_data = {
        "_id":uuid.uuid4().hex,
        "protocol": name,
        "symbol":combined_list[encoded_name],
        "reportContent": report_html,
        "userId": user_id,
        "createdAt": datetime.datetime.utcnow()
    }
    # Store in MongoDB
    db.reports.insert_one(report_data)
    session.pop("payment_verified", None)
    return jsonify({"message": "Report generated successfully.", "report": report_data})

@app.route("/my-agent-flows")
@login_required
def my_agent_flows():
    """Fetch all agent flows and executed swaps for the user."""
    user_id = session.get("wallet_address")
    if not user_id:
        return redirect(url_for("login"))

    agent_flows = list(db.agent_flows.find({"user_id": user_id}, {"_id": 1, "target_security_score": 1, "top_n": 1, "created_at": 1}))
    executed_swaps = list(db.executed_swaps.find({"user_id": user_id}, {"_id": 0}))

    return render_template("my-agent-flows.html", agent_flows=agent_flows, executed_swaps=executed_swaps)

@app.route("/set-agent-flow", methods=["POST"])
@login_required
def set_agent_flow():
    """Save user-defined agent flow for automated rebalancing."""
    user_id = session.get("wallet_address")
    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    data = request.get_json()
    target_security_score = data.get("target_security_score")
    top_n = data.get("top_n")
    if not target_security_score or not top_n:
        return jsonify({"error": "Invalid input data"}), 400
    agent_flow = {
        "_id": uuid.uuid4().hex,
        "user_id": user_id,
        "target_security_score": target_security_score,
        "top_n": top_n,
        "created_at": datetime.datetime.utcnow()
    }
    db.agent_flows.insert_one(agent_flow)
    return jsonify({"message": "Agent flow saved successfully"})

import copy
@app.route("/execute-agent-flow", methods=["POST"])
@login_required
def execute_agent_flow():
    """Execute the selected agent flow for the user with real-time holdings and private key authentication."""
    user_id = session.get("wallet_address")
    if not user_id:
        return jsonify({"message": "User not authenticated"}), 401

    data = request.get_json()
    flow_id = data.get("flow_id")
    private_key = data.get("private_key")

    if not flow_id or not private_key:
        return jsonify({"message": "Flow ID and private key are required"}), 400

    # Verify private key
    try:
        account = Account.from_key(private_key)
        if account.address.lower() != user_id.lower():
            return jsonify({"message": "Private key does not match the wallet address"}), 403
    except Exception:
        return jsonify({"message": f"Invalid private key: {str(e)}"}), 403

    # Fetch agent flow
    flow = db.agent_flows.find_one({"_id": flow_id, "user_id": user_id})
    if not flow:
        return jsonify({"message": "Agent flow not found"}), 404

    # Fetch current token holdings
    user_tokens = get_tokens_held("sonic", user_id, os.getenv("SONIC_API_KEY"))
    if not user_tokens or isinstance(user_tokens, dict):
        return jsonify({"message": "No tokens found or an error occurred."}), 400

    protocols_data = []
    total_portfolio_value = 0

    # Process tokens and calculate portfolio distribution
    for token in user_tokens:
        protocol_stats = dashboard_stats(token["name"], token["symbol"])
        token_price = protocol_stats.get("tokenStats", {}).get("price_usd", 0)
        token_value = token["balance"] * token_price

        token["value_usd"] = round(token_value, 2)
        token["price_usd"] = round(token_price, 4)
        token["contract_address"] = token["contract_address"]
        total_portfolio_value += token_value

        token.update(protocol_stats)
        protocols_data.append(token)

    # Calculate percentage holdings
    for token in protocols_data:
        token["holding_percent"] = round((token["value_usd"] / total_portfolio_value) * 100, 2) if total_portfolio_value > 0 else 0

    current_holdings = copy.deepcopy(protocols_data)

    # Perform rebalancing
    rebalanced_tokens = rebalance_portfolio(copy.deepcopy(current_holdings), float(flow["target_security_score"]), private_key, int(flow["top_n"]))

    if not isinstance(rebalanced_tokens, list):
        return jsonify({"message": rebalanced_tokens["result"]}), 400

    new_holdings = copy.deepcopy(rebalanced_tokens)

    # Check if rebalancing made any changes
    if new_holdings == current_holdings:
        return jsonify({"message": "No changes were made during rebalancing."}), 400

    # Store executed swap with correct original and new holdings
    executed_swap = {
        "_id": uuid.uuid4().hex,
        "user_id": user_id,
        "original_holdings": copy.deepcopy(current_holdings),
        "new_holdings": new_holdings,
        "executed_at": datetime.datetime.utcnow()
    }
    db.executed_swaps.insert_one(executed_swap)

    return jsonify({"message": "Agent flow executed and swaps processed successfully.", "updated_holdings": new_holdings})
@app.route("/log-out")
@login_required
def log_out():
    session.clear()
    return redirect(url_for("dashboard"))

# Function to read and convert Markdown to HTML using markdown2
def get_markdown_content(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return markdown2.markdown(content)

@app.route("/zerepy-docs")
def zerepy_docs():
    zerepy_content = get_markdown_content("zerepy_docs.md")
    return render_template("zerepy-docs.html",zerepy_content=zerepy_content)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
