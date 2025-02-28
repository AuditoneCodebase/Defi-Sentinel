from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_session import Session
from utils.db_client import client
from web3 import Web3
import datetime
import uuid
import functools
from assessment.agent_choice import fetch_complete_data
from assessment.user_tokens import fetch_user_and_project_data
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
users = db["users"]

# Web3 Configuration for Base Network
BASE_RPC_URL = "https://mainnet.base.org"
AUDIT_TOKEN_CONTRACT = "0xYourAuditTokenContractAddress"
AUDIT_TOKEN_DECIMALS = 18
WEB3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
AUDIT_TOKEN_COST = Web3.to_wei(1, "ether")  # Cost: 1 AUDIT tokens
ACCESS_DURATION = 30  # Days to allow access after payment

# Register the custom markdown filter
@app.template_filter('markdown')
def markdown_filter(text):
    return markdown2.markdown(text)

# **Authentication Decorator**
def login_required(f):
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        if "wallet_address" not in session:
            return jsonify({"error": "Unauthorized access"})
        return f(*args, **kwargs)

    return wrap


# **Render the Frontend**
@app.route("/")
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

    return jsonify({"message": "Wallet address stored", "redirect": "/dashboard"})


# **Get Stored Wallet Address**
@app.route("/dashboard")
@login_required
def dashboard():
    protocols_data = fetch_complete_data()  # Example function fetching the data

    if isinstance(protocols_data, str):  # Convert if it's a JSON string
        import json
        protocols_data = json.loads(protocols_data)

    return render_template("dashboard.html", protocols=protocols_data)


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
    # Fetch the data
    data = fetch_user_and_project_data("sonic", session["wallet_address"], os.getenv("SONIC_API_KEY"))

    # Check if data is a string (i.e., JSON string)
    if isinstance(data, str):
        tokens_data = json.loads(data)
    else:
        tokens_data = data

    # Check for errors in the data
    if "error" in tokens_data:
        return render_template("my-tokens.html", message="error")

    # Render template with the token data
    return render_template("my-tokens.html", data=tokens_data)


@app.route("/analyze-token")
@login_required
def analyze_token():
    return render_template("analyze-token.html")

@app.route("/about-us")
def about_us():
    return render_template("about-us.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
