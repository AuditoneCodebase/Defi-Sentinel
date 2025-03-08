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
from assessment.agent_choice import project_list, project_for_dashboard
from openai import OpenAI
from dotenv import load_dotenv
import os
import markdown2
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
    user_tokens = get_tokens_held("sonic",session["wallet_address"],os.getenv("SONIC_API_KEY"))
    if len(user_tokens)==0 or type(user_tokens)==dict:
        return render_template("my-tokens.html",message="error")
    else:
        protocols_data = []
        for protocol in user_tokens:
            protocol_stats = dashboard_stats(protocol["name"],protocol["symbol"])
            protocols_data.append(protocol_stats)
        return render_template("my-tokens.html",protocols=protocols_data)

@app.route("/analyze-token")
@login_required
def analyze_token():
    # Merge `projects_list` and `user_tokens` without duplicates
    combined_tokens = {name: symbol for name, symbol in project_list.items()}  # Add all projects
    user_tokens = get_tokens_held("sonic", session["wallet_address"], os.getenv("SONIC_API_KEY"))
    if len(user_tokens)==0 or type(user_tokens)==dict:
        pass
    else:
        for token in user_tokens:
            combined_tokens[token["name"]] = token["symbol"]  # Ensure user-selected tokens are included
    session["combined_tokens"] = combined_tokens
    return render_template("analyze-token.html", combined_tokens=combined_tokens)

def validate_payment(tx_hash):
    """
    Validate if the transaction meets payment requirements.
    """
    try:
        tx = WEB3.eth.get_transaction(tx_hash)
        receipt = WEB3.eth.get_transaction_receipt(tx_hash)
    except Exception:
        return {"status": "failed", "reason": "Transaction not found."}

    if receipt["status"] != 1 or tx["to"].lower() != RECIPIENT_ADDRESS.lower() or tx["value"] < SONIC_NATIVE_TOKEN_COST:
        return {"status": "failed", "reason": "Invalid payment."}

    return {"status": "success", "sender": tx["from"], "tx_hash": tx_hash}

@app.route("/process-payment", methods=["POST"])
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

@app.route("/generate-report/<symbol>", methods=["GET"])
def generate_report(symbol):
    """
    Generates a risk analysis report only if payment is confirmed.
    """
    if not session.get("payment_verified"):
        return jsonify({"error": "Payment required before analysis."}), 403

    # Mock analysis result
    report_data = {
        "token": symbol,
        "riskScore": "Medium",
        "volatility": "High",
        "liquidityRisk": "Low",
        "marketSentiment": "Bullish",
        "reportContent": f"Analysis report for {symbol}: This token has medium risk, high volatility, and low liquidity risk.",
        "userId": session["wallet_address"],
        "createdAt":datetime.datetime.utcnow()
    }

    # Store in MongoDB
    db.reports.insert_one(report_data)

    return jsonify(report_data)

@app.route("/my-reports")
@login_required
def my_reports():
    """
    Fetch all reports for the user.
    """
    reports = list(db.reports.find({"userId":session["wallet_address"]}, {"_id": 0}))  # Hide MongoDB _id field
    return render_template("my-reports.html", reports=reports)

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
