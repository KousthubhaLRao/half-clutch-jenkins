import redis #

# Connect to Redis
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def enqueue_job(job_id, priority):
    """
    Adds a job to a Sorted Set. 
    A higher priority value (3) will be processed before lower values (1).
    """
    # We use zadd with a mapping of {member: score}
    # Using the priority as the score
    r.zadd("job_priority_queue", {job_id: priority})