from utils.db_client import client
db = client["agentDatabase"]

def get_audit_security_score(project_name):
    """
    Fetches audit data for a given project from MongoDB and calculates a security score
    based on the number of audits.
    """

    # Fetch audits related to the project
    audits = list(db.auditReports.find(
        {"fileName": {"$regex": project_name, "$options": "i"}},
        {"_id": 0, "source": 1}  # Fetch only the 'source' field
    ))

    audit_sources = {}

    # Group audits by source
    for audit in audits:
        source = audit.get("source", "Unknown")
        if source not in audit_sources:
            audit_sources[source] = []
        audit_sources[source].append(audit)

    # Count total audits
    total_audits = sum(len(audits) for audits in audit_sources.values())

    # Determine security score based on audit count
    if total_audits == 0:
        total_score = 0
    elif total_audits == 1:
        total_score = 50
    elif total_audits >= 8:
        total_score = 99
    else:
        total_score = 50 + ((total_audits - 1) * (50 / 7))  # Scale between 50-100

    return {
        "project_name": project_name,
        "audited_by": list(audit_sources.keys()),
        "total_audits": total_audits,
        "total_score": round(total_score, 2)
    }

def fetch_hacks_from_database(project_name):
    """
    Fetches past hacks related to the given protocol from MongoDB and categorizes them by source.
    """
    # Query the database for hacks related to the project
    hacks = list(db.previousHacks.find(
        {"protocol": {"$regex": project_name, "$options": "i"}},
        {"_id": 0, "date": 1, "protocol": 1, "amountLost": 1, "attackMethod": 1, "description": 1, "source": 1, "sourceType": 1}
    ))

    # Categorize hacks into different sources
    categorized_hacks = {
        "projectName": project_name,
        "slowmist": [],
        "rekt_news": []
    }

    # Process hacks
    for hack in hacks:
        hack_entry = {
            "date": hack.get("date", "Unknown Date"),
            "protocol": hack.get("protocol", "Unknown Protocol"),
            "amountLost": hack.get("amountLost", "N/A"),
            "attackMethod": hack.get("attackMethod", "Unknown"),
            "description": hack.get("description", "No description available"),
            "source": hack.get("source", "No link available")
        }

        # Classify hacks by source type
        source_type = hack.get("sourceType")
        if source_type == "SlowMist":
            categorized_hacks["slowmist"].append(hack_entry)
        if source_type == "Rekt.News":
            categorized_hacks["rekt_news"].append(hack_entry)


    # Handle cases where no hacks were found
    for key in ["slowmist", "rekt_news"]:
        if not categorized_hacks[key]:
            categorized_hacks[key] = {"message": "No hacks found"}

    return categorized_hacks


