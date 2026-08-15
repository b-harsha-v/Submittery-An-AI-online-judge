import redis
import json
from ..config import settings

# Setup standard Redis client (using host port 6385 as configured in settings)
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

class QueueService:
    @staticmethod
    def push_submission(submission_id: str) -> int:
        """
        Pushes the submission UUID to the Redis queue.
        Returns the number of elements in the queue after push.
        """
        return redis_client.rpush("submissions_queue", submission_id)
        
    @staticmethod
    def publish_status_update(submission_id: str, status: str, runtime: float = None, memory: int = None, error_message: str = None, results: list = None):
        """
        Publishes a JSON payload containing the updated status to the Redis Pub/Sub channel.
        FastAPI WebSocket handler will listen to this channel and push to the frontend.
        """
        payload = {
            "submission_id": submission_id,
            "status": status,
            "runtime": runtime,
            "memory": memory,
            "error_message": error_message,
            "results": results
        }
        redis_client.publish("submission_status_updates", json.dumps(payload))

queue_service = QueueService()
