import os
import subprocess
import time
import uuid
from datetime import datetime

# CONFIGURATION: 3 Repos, 2 Branches each = 6 Targets
# PATHS UPDATED FOR: /home/shreeharsha/Desktop/Devops/
HARVEST_FIELDS = [
    # Repository 1: Python
    {"name": "Python-PROD", "path": "/home/shreeharsha/Desktop/Devops/half-clutch-jenkins", "branch": "main", "prio": "P3"},
    {"name": "Python-STAGING", "path": "/home/shreeharsha/Desktop/Devops/half-clutch-jenkins", "branch": "staging", "prio": "P2"},
    
    # Repository 2: CPP
    {"name": "CPP-PROD", "path": "/home/shreeharsha/Desktop/Devops/neetcode-submissions-x613f09a", "branch": "main", "prio": "P3"},
    {"name": "CPP-DEVELOP", "path": "/home/shreeharsha/Desktop/Devops/neetcode-submissions-x613f09a", "branch": "develop", "prio": "P2"},
    
    # Repository 3: Web
    {"name": "Web-PROD", "path": "/home/shreeharsha/Desktop/Devops/kousthubha-site", "branch": "main", "prio": "P3"},
    {"name": "Web-FEATURE", "path": "/home/shreeharsha/Desktop/Devops/kousthubha-site", "branch": "feature-v1", "prio": "P1"}
]

def execute_harvest(field, count):
    repo_path = field['path']
    branch = field['branch']
    job_token = f"{field['prio']}-{uuid.uuid4().hex[:5]}"
    
    if not os.path.exists(repo_path):
        print(f"❌ Path missing: {repo_path}")
        return

    tracker_path = os.path.join(repo_path, "harvest_tracker.txt")
    
    print(f"[{count}/15] 🚜 Harvesting {field['name']} ({branch}) | {field['prio']}...")
    
    try:
        # Switch branch, write unique token, commit, and push
        subprocess.run(f"git checkout {branch}", cwd=repo_path, shell=True, check=True, capture_output=True)
        
        with open(tracker_path, "a") as f:
            f.write(f"Storm {count} | Token: {job_token} | {datetime.now()}\n")

        subprocess.run("git add harvest_tracker.txt", cwd=repo_path, shell=True, check=True, capture_output=True)
        subprocess.run(f'git commit -m "Storm {count}: {job_token}"', cwd=repo_path, shell=True, check=True, capture_output=True)
        subprocess.run(f"git push origin {branch}", cwd=repo_path, shell=True, check=True, capture_output=True)
        print(f"   ✅ Sent: {job_token}")

    except subprocess.CalledProcessError as e:
        print(f"   ❌ Git Error on {branch}: {e.stderr.decode().strip()}")

if __name__ == "__main__":
    print("═══ STARTING THE 15-COMMIT CATEGORY 5 STORM ═══")
    print("🚨 REMINDER: SHUT DOWN YOUR WORKERS BEFORE RUNNING THIS!\n")
    time.sleep(2)

    counter = 1

    # PHASE 1: 5 LOW PRIORITY (P1) - The "Bottom of the Stack"
    print("\n--- PHASE 1: CLOGGING THE QUEUE WITH LOW PRIORITY (P1) ---")
    for _ in range(5):
        execute_harvest(HARVEST_FIELDS[5], counter) # Web Feature
        counter += 1
        time.sleep(1)

    # PHASE 2: 5 MEDIUM PRIORITY (P2) - The "Middle Tier"
    print("\n--- PHASE 2: INJECTING MEDIUM PRIORITY (P2) ---")
    for _ in range(3):
        execute_harvest(HARVEST_FIELDS[1], counter) # Python Staging
        counter += 1
    for _ in range(2):
        execute_harvest(HARVEST_FIELDS[3], counter) # CPP Develop
        counter += 1

    # PHASE 3: 5 HIGH PRIORITY (P3) - The "Line Jumpers"
    print("\n--- PHASE 3: SENDING THE ELITE HIGH PRIORITY (P3) ---")
    execute_harvest(HARVEST_FIELDS[0], counter); counter += 1 # Python Main
    execute_harvest(HARVEST_FIELDS[2], counter); counter += 1 # CPP Main
    execute_harvest(HARVEST_FIELDS[4], counter); counter += 1 # Web Main
    execute_harvest(HARVEST_FIELDS[0], counter); counter += 1 # Python Main (again)
    execute_harvest(HARVEST_FIELDS[2], counter); counter += 1 # CPP Main (again)

    print("\n" + "="*55)
    print(f"🏁 15 COMMITS DEPLOYED. THE FIELDS ARE OVERFLOWING!")
    print("INSTRUCTIONS:")
    print("1. Check 'The Loom' Dashboard. You should see 15 Queued jobs.")
    print("2. The P1 jobs will likely be at the TOP of your UI list.")
    print("3. START THE WORKER MANAGER NOW.")
    print("4. WATCH: The P3 jobs will be snatched first!")
    print("="*55)