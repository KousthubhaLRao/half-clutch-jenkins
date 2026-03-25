import redis # type: ignore

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def enqueue_job(job_id):
    r.lpush("job_queue", job_id)