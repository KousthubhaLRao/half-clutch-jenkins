import os
import subprocess
import datetime
import time
import random

# 1. YOUR LINUX PATHS
REPOS = [
    "/home/shreeharsha/Desktop/Devops/neetcode-submissions-x613f09a",
    "/home/shreeharsha/Desktop/Devops/kousthubha-site",
    "/home/shreeharsha/Desktop/Devops/half-clutch-jenkins"
]

def run_git_command(command, repo_path):
    try:
        result = subprocess.run(
            command, cwd=repo_path, shell=True, 
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return f"❌ Error: {result.stderr.strip()}"
        return result.stdout.strip()
    except Exception as e:
        return f"❌ System Error: {e}"

def clear_screen():
    os.system('clear')

def harvest_with_chaos():
    clear_screen()
    print("🌪️  STARTING THE CHAOTIC TRIPLE HARVEST...")
    print("="*55)
    
    # 1. Decide on a total number of jobs (6 to 10)
    total_jobs_count = random.randint(6, 10)
    
    # 2. Build the task list: Start with one push for each repo to ensure coverage
    task_list = REPOS.copy()
    
    # 3. Fill the remaining spots randomly
    while len(task_list) < total_jobs_count:
        task_list.append(random.choice(REPOS))
    
    # 4. Shuffle them so the dashboard looks busy and unpredictable
    random.shuffle(task_list)

    print(f"📊 Planning to dispatch {total_jobs_count} bales across the fields.")
    print(f"🏢 Total Workers: 5 | Specialty matching enabled.")
    print("="*55 + "\n")

    for i, repo_path in enumerate(task_list, 1):
        repo_name = os.path.basename(repo_path)
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        print(f"[{i}/{total_jobs_count}] 🚜 Tilling {repo_name}...")

        # Create a real change in the log file
        log_file = os.path.join(repo_path, "harvest_log.txt")
        with open(log_file, "a") as f:
            f.write(f"Chaos job {i} triggered at {timestamp}\n")

        # Execute Git flow
        print("   - Adding & Committing...")
        run_git_command("git add harvest_log.txt", repo_path)
        run_git_command(f'git commit -m "Chaos harvest {i} at {timestamp}"', repo_path)
        
        print("   - Pushing to GitHub...")
        push_output = run_git_command("git push origin main", repo_path)
        
        if "Error" in push_output:
            print(f"   {push_output}")
        else:
            print(f"   ✅ Dispatched successfully!")
        
        print("-" * 35)
        
        # Real-world delay: random wait between 1 and 3 seconds
        time.sleep(random.uniform(1.0, 3.0))

    print("\n🏁 CHAOS COMPLETE.")
    print(f"Go to the Dashboard to see your {total_jobs_count} jobs being ginning!")

if __name__ == "__main__":
    harvest_with_chaos()