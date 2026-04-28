import os
import subprocess
import time
import random
from datetime import datetime

# 1. CONFIGURATION - Update these paths to your actual local folders!
REPOS = [
    {
        "name": "Python Repo",
        "path": r"C:\Users\koust\Desktop\half-clutch-jenkins",
        "branch": "main"
    },
    {
        "name": "CPP Repo",
        "path": r"C:\Users\koust\Desktop\neetcode-submissions-x613f09a",
        "branch": "main"
    },
    {
        "name": "Web/CSS Repo",
        "path": r"C:\Users\koust\Desktop\kousthubha-site",
        "branch": "main"
    }
]

def run_command(cmd, repo_path):
    """Executes a git command in the specific repo folder."""
    result = subprocess.run(cmd, cwd=repo_path, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr.strip()}")
    return result.returncode == 0

def push_real_harvest():
    # Pick a random repo to "till"
    repo = random.choice(REPOS)
    print(f"\n🚜 Starting automated harvest for: {repo['name']}...")

    # 1. Create/Update a harvest log file to ensure there is a change to push
    log_file = os.path.join(repo['path'], "harvest_tracker.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_file, "a") as f:
        f.write(f"Automated harvest event at {timestamp}\n")

    # 2. Perform the Git workflow
    print(f"  - Committing changes...")
    if run_command("git add harvest_tracker.txt", repo['path']):
        commit_msg = f"Automated harvest {timestamp}"
        if run_command(f'git commit -m "{commit_msg}"', repo['path']):
            print(f"  - Pushing to GitHub...")
            if run_command(f"git push origin {repo['branch']}", repo['path']):
                print(f"✅ REAL PUSH SUCCESSFUL: {repo['name']}")
            else:
                print("❌ Push failed. Check your internet or git credentials.")

if __name__ == "__main__":
    print("🚀 AUTOMATED HARVESTER ACTIVE")
    print("This script will make ACTUAL pushes to your GitHub repos.")
    
    try:
        # We will do 5 random pushes to demonstrate the system
        for i in range(5):
            push_real_harvest()
            
            # Random wait between 10 and 30 seconds to avoid GitHub spam blocks
            wait = random.randint(10, 30)
            print(f"⏳ Waiting {wait}s before the next random push...")
            time.sleep(wait)
            
    except KeyboardInterrupt:
        print("\n🏁 Harvester stopped by user.")