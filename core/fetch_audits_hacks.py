from utils.db_client import client
db = client["agentDatabase"]

def get_audit_security_score(project_name):
    """
    Fetches audit data for a given project from MongoDB (db.auditReports)
    and calculates a security score based on audits and their sources.
    """

    # Fetch audits related to the project by filename (case-insensitive)
    audits = list(db.auditReports.find(
        {"fileName": {"$regex": project_name, "$options": "i"}},
        {"_id": 0, "source": 1}  # Fetch only the 'source' field
    ))

    # Group audits by source
    audit_sources = {}
    for audit in audits:
        source = audit.get("source", "Unknown")
        audit_sources.setdefault(source, []).append(audit)

    # Scoring weights
    scores = {
        'Code4rena': 93,
        'Sherlock': 90,
        'Solidproof': 20,
        'Pashov': 78,
        'Cyfrin': 95,
        'Cantina': 95,
        'Zokyo': 75,
        'AuditOne': 80,
        'Certik': 30
    }

    # These sources count each audit as half
    half_weight_projects = ['Sherlock', 'Code4rena']

    # Accumulate total audits & track sources
    total_audits = 0
    audited_by = []

    for source, data in audit_sources.items():
        if len(data) > 0:
            audited_by.append(source)
            # Apply half-weight if source is in half_weight_projects
            if source in half_weight_projects:
                total_audits += len(data) // 2
            else:
                total_audits += len(data)

    # --- Calculate the score ---
    if total_audits >= 8:
        # If total audits >= 8, cap at 100
        total_score = 100
    elif total_audits == 1:
        # If exactly 1 audit, use that source's score (default 50 if missing)
        if audited_by:
            total_score = scores.get(audited_by[0], 50)
        else:
            total_score = 50
    elif total_audits == 0:
        # No audits
        total_score = 0
    else:
        # Multiple audits but fewer than 8
        audited_weights = [scores.get(source, 50) for source in audited_by]
        if not audited_weights:
            # No known sources => 0
            return {
                "project_name": project_name,
                "audited_by": [],
                "total_audits": total_audits,
                "total_score": 0
            }

        # Weighted combination: 80% from the highest score, 20% from the lowest
        max_score = max(audited_weights)
        min_score = min(audited_weights)
        total_score = (0.8 * max_score) + (0.2 * min_score)

    return {
        "project_name": project_name,
        "audited_by": audited_by,
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


