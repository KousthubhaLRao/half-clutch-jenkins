import os
import subprocess
import time
import random
from datetime import datetime

REPOS = [
    {"name": "Python", "path": r"C:\Users\koust\Desktop\half-clutch-jenkins", "branch": "main"},
    {"name": "CPP", "path": r"C:\Users\koust\Desktop\neetcode-submissions-x613f09a", "branch": "main"},
    {"name": "Web", "path": r"C:\Users\koust\Desktop\kousthubha-site", "branch": "main"}
]

def push_real_harvest():
    repo = random.choice(REPOS)
    log_file = os.path.join(repo['path'], "harvest_tracker.txt")
    timestamp = datetime.now().strftime("%H:%M:%S.%f")
    
    with open(log_file, "a") as f:
        f.write(f"Flood push at {timestamp}\n")

    subprocess.run("git add harvest_tracker.txt", cwd=repo['path'], shell=True, capture_output=True)
    subprocess.run(f'git commit -m "Flood {timestamp}"', cwd=repo['path'], shell=True, capture_output=True)
    
    # Run the push
    print(f"🚜 Tilling {repo['name']} field...")
    subprocess.run(f"git push origin {repo['branch']}", cwd=repo['path'], shell=True, capture_output=True)

if __name__ == "__main__":
    print("🌊 STARTING THE HARVEST FLOOD...")
    # Fire off 15 pushes as fast as GitHub will allow (usually 1-2 seconds per push)
    for i in range(15):
        push_real_harvest()
        # Minimal wait just to let the terminal breathe
        time.sleep(1) 
    
    print("\n🏁 Flood complete. Check the Loom!")