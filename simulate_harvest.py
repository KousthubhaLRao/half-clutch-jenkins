import requests
import time
import random
import uuid

# The API endpoint where your Master is listening
API_URL = "http://127.0.0.1:8000/webhook"

# Your actual repositories for testing
HARVEST_SOURCES = [
    {"repo": "KousthubhaLRao/half-clutch-jenkins", "branch": "refs/heads/main"},
    {"repo": "KousthubhaLRao/neetcode-submissions-x613f09a", "branch": "refs/heads/main"},
    {"repo": "KousthubhaLRao/kousthubha-site", "branch": "refs/heads/main"}
]

def simulate_push():
    """Simulates a single Git push event hitting the Master."""
    source = random.choice(HARVEST_SOURCES)
    
    payload = {
        "repository": {
            "full_name": source["repo"] #
        },
        "ref": source["branch"], #
        "after": uuid.uuid4().hex[:8] # Random commit SHA
    }

    print(f"🌾 Gathering a new bale from: {source['repo']}...")
    
    try:
        # Sending the POST request to your FastAPI Master
        response = requests.post(API_URL, json=payload, timeout=5)
        if response.status_code == 200:
            job_id = response.json().get("job_id")
            print(f"✅ Harvest accepted! Job ID: {job_id}")
        else:
            print(f"❌ Field error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ The Master is not responding: {e}")

if __name__ == "__main__":
    print("🚀 Starting Harvest Simulation (Ctrl+C to stop)...")
    
    # Simulate a burst of activity to test Priority and Worker Assignment
    num_jobs = 15
    for i in range(num_jobs):
        simulate_push()
        
        # Real-world randomness: arrival between 1 and 4 seconds
        wait_time = random.uniform(1.0, 4.0)
        print(f"⏳ Waiting {wait_time:.1f}s for the next harvest arrival...")
        time.sleep(wait_time)

    print("\n🏁 All simulated cotton bales have been sent to the Loom!")