import uuid
from assessment.agent_choice import fetch_complete_data
from utils.db_client import client
from openai import OpenAI
import datetime
import json

openai_client = OpenAI()

db = client["agentDatabase"]

def push_report_to_db(project_name):
    protocols_data = fetch_complete_data()  # Fetch stored DeFi data

    # Convert string to dictionary if needed
    if isinstance(protocols_data, str):
        protocols_data = json.loads(protocols_data)

    # Retrieve project data
    protocol = protocols_data.get(project_name)

    # Extract details with safe defaults
    audit_security = protocol.get("auditSecurityScore", {})
    past_hacks = protocol.get("pastHacks", {})
    tvl_metrics = protocol.get("tvlMetrics", {})

    # Construct AI prompt
    prompt = f"""
    Analyze the following DeFi project and provide a security and risk assessment:

    **Project Name:** {audit_security.get("project_name", "Unknown")}
    **Audit Security Score:** {audit_security.get("total_score", "Not Available")}
    **Audited By:** {", ".join(audit_security.get("audited_by", [])) if audit_security.get("audited_by") else "None"}
    **Past Hacks:** {json.dumps(past_hacks, indent=2)}

    **Key Metrics:**
    - TVL (Total Value Locked): ${tvl_metrics.get("totalTvl", "Unknown")}
    - Average APY: {tvl_metrics.get("avgApy", "Unknown")}%
    - Impermanent Loss Risk: {"Yes" if tvl_metrics.get("impermanentLossRisk", 0) > 0 else "No"}
    - Number of Pools: {tvl_metrics.get("numPools", "Unknown")}
    - Predicted Probability of Decline: {tvl_metrics.get("predictedProbability", "Unknown")}%

    Provide an expert-level risk analysis for users interacting with protocol including security insights, investment risks, and any other.
    If audits count is 0, you do not have data but it does not indicate that there are no audits done for the project.
    """
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a DeFi security expert."},
            {"role": "user", "content": prompt}
        ]
    )
    ai_report = response.choices[0].message.content

    db.aiReports.insert_one({"_id":uuid.uuid4().hex,"aiReport":ai_report,"project":project_name,"createdAt":datetime.datetime.utcnow()})

