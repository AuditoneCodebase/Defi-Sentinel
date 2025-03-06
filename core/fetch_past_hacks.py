# without zerepy

from utils.db_client import client
db = client["agentDatabase"]

def hacks_data(project_name):
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
