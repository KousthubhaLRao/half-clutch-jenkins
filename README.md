# Half Clutch Jenkins (Mini CI/CD)

A simplified Jenkins-like CI/CD system implementing the core “master” functionality: webhook ingestion, job storage, queuing, and execution.

hehehehe

---

## Tech Stack

* FastAPI
* PostgreSQL
* Redis
* SQLAlchemy
* Docker

---

## Project Structure

```
half-clutch-jenkins/
├── app/
│   ├── main.py
│   ├── db.py
│   ├── models/
│   │   └── job.py
│   ├── jobs/
│   │   └── queue.py
│   └── pipeline/
│       └── executor.py
├── docker-compose.yml
├── requirements.txt
└── .gitignore
```

---

## Setup

1. Clone the repo:

```
git clone https://github.com/YOUR_USERNAME/half-clutch-jenkins.git
cd half-clutch-jenkins
```

2. Install dependencies:

```
pip install -r requirements.txt
```

3. Start services:

```
docker compose up -d
```

4. Run API server:

```
python -m uvicorn app.main:app --reload
```

5. Run executor (in a new terminal):

```
python -m app.pipeline.executor
```

---

## Usage

Open:

```
http://127.0.0.1:8000/docs
```

Send POST request to `/webhook` with:

```
{
  "repository": {
    "full_name": "test/repo"
  },
  "ref": "refs/heads/main",
  "after": "abc123"
}
```

---

## Verify

Check jobs in database:

```
docker exec -it half-clutch-jenkins-postgres-1 psql -U jenkins -d jenkins_db
```

```
SELECT * FROM jobs;
```

---

## Notes

* Jobs move through: `queued → running → completed`
* Pipeline execution is simulated
* Only Jenkins master functionality is implemented (no workers)
