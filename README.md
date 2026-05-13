
# 🌾 Half Clutch-CI/CD System

The **Half Clutch-CI/CD System** is a resilient, asynchronous pipeline orchestrator designed to handle high-volume build requests. It leverages a multi-tier architecture to decouple build ingestion from execution, ensuring production-critical code is prioritized and processed in isolated environments.

## 🚀 Key Features

* **Strategic Priority Scheduling**: Uses **Redis Sorted Sets** to implement a branch-based scoring model. Builds for `main` or `master` branches (Priority 3) automatically leapfrog feature branches (Priority 1) in the queue.
* **Specialized Harvester Pool**: A multi-threaded execution tier featuring specialized "Harvester" threads for Python, C++, and JavaScript. It includes a "General Laborer" fallback for non-specialized tasks.
* **Workspace Isolation**: Every job is executed in a unique, isolated directory located at `/tmp/half-clutch/workspaces/`. These workspaces are automatically purged upon completion to prevent disk-space leaks and cross-build contamination.
* **The Loom Dashboard**: A real-time observability interface powered by **FastAPI WebSockets**. It provides instant updates on job transitions and build progress without requiring manual page refreshes.
* **Resilient Reaper Mechanism**: A background monitor that identifies orphaned jobs from crashed worker threads using a `last_heartbeat` timestamp. Orphaned jobs are automatically re-enqueued to ensure zero-loss reliability.
* **Deduplication Engine**: Validates incoming `commit_sha` metadata to prevent redundant processing of duplicate webhook signals.

## 🛠️ Tech Stack

* **Backend**: FastAPI (Python)
* **Messaging/Queuing**: Redis (Sorted Sets)
* **Database**: PostgreSQL (SQLAlchemy ORM)
* **Frontend**: WebSocket-driven HTML5 Dashboard
* **Infrastructure**: Docker Compose

## 📁 Project Structure

```text
half-clutch-jenkins/
├── app/
│   ├── main.py            # Master API, Priority Logic, & WebSockets
│   ├── db.py              # PostgreSQL connection management
│   ├── models/
│   │   └── job.py         # Job Schema & Heartbeat tracking
│   ├── jobs/
│   │   └── queue.py       # Redis Priority Queue logic
│   └── pipeline/
│       └── worker_manager.py # Multi-threaded Harvesters & Reaper
├── triple_harvester.py    # 15-Commit Strategic Storm Stress Test
├── docker-compose.yml     # Redis & Postgres orchestration
└── requirements.txt       # Project dependencies

```

## ⚙️ Setup & Installation

1. **Start Infrastructure**:
Launch the required Redis and PostgreSQL services using Docker:
```bash
docker compose up -d

```


2. **Launch the Master API**:
Start the FastAPI server:
```bash
export PYTHONPATH=$PYTHONPATH:.
python3 -m uvicorn app.main:app --reload

```


3. **Initialize the Harvester Pool**:
In a separate terminal, start the worker manager:
```bash
export PYTHONPATH=$PYTHONPATH:.
python3 -m app.pipeline.worker_manager

```



## 🧪 Demonstration: The "Priority Jump"

To validate the system's scheduling intelligence as described in the project report:

1. **Stop the Worker Manager** (`Ctrl+C`) to allow the queue to fill.
2. **Run the Strategic Storm**: Execute `python3 triple_harvester.py`. This script pushes 15 commits, starting with Low Priority (P1) and ending with High Priority (P3).
3. **Monitor "The Loom"**: Navigate to `http://localhost:8000/dashboard`. Observe 15 jobs queued; the P3 jobs will be sorted to the top.
4. **Restart the Worker Manager**: Watch as the workers immediately snatch the **High Priority (P3)** jobs first, regardless of their arrival time.