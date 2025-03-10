import requests

def load_agent():
    """Ensures the agent is loaded before fetching token stats."""
    url = "https://zerepy.auditone.io/agents/auditone-sonic/load"
    headers = {
        "accept": "application/json"
    }

    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        return True  # Agent loaded successfully
    else:
        print(f"Error loading agent: {response.status_code}")
        return False  # Failed to load agent

def stats_by_project(project_name):
    """Fetches token stats after ensuring the agent is loaded."""
    if not load_agent():
        return {"error": "Failed to load agent", "default_used": True}

    url = "https://zerepy.auditone.io/agent/action"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {
        "connection": "sonic",
        "action": "get-security-stats",
        "params": [project_name]
    }

    response = requests.post(url, headers=headers, json=data)


    if response.status_code == 200:
        result = response.json()

        # If API returns an error, use default values
        if result.get("status") == "error":
            result = {"status": "error", "result": {}}
            return result
        else:
            audit_data = result.get("result")["audit_data_stats"]
            hacks_data = result.get("result")["previous_hacks_stats"]
            return {
                "project_name": project_name,
                "audit_data": audit_data,
                "hacks_data":hacks_data
            }

