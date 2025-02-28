import requests
from utils.db_client import client
import uuid

db=client["agentDatabase"]

# API URL for fetching TVL data
API_URL = "https://yields.llama.fi/pools"


def fetch_sonic_tvl():
    """
    Fetches TVL data from DeFi Llama and filters Sonic chain pools.
    """
    try:
        response = requests.get(API_URL, headers={"accept": "*/*"})
        if response.status_code == 200:
            data = response.json()["data"]

            # Filter for Sonic chain pools
            sonic_pools = [pool for pool in data if pool.get("chain") == "Sonic"]

            if not sonic_pools:
                print("No Sonic pools found.")
                return

            for pool in sonic_pools:
                pool["_id"] = str(uuid.uuid4().hex)  # Assign unique UUID
                db.tvlSonicProjects.update_one({"_id": pool["_id"]}, {"$set": pool}, upsert=True)

            print(f"Inserted {len(sonic_pools)} Sonic pools into MongoDB.")

        else:
            print(f"Failed to fetch data. Status Code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print("Error fetching TVL data:", str(e))

