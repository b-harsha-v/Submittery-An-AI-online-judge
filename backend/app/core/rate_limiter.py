import time
from fastapi import Request, HTTPException, status
from typing import Optional
from ..services.queue_service import redis_client

class RateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int, scope: str = "general"):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.scope = scope
        self.memory_store = {}

    def __call__(self, request: Request):
        # Identify client by user_id if token is present, otherwise client IP
        client_id = request.client.host if request.client else "unknown_client"
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                from ..security import decode_token
                payload = decode_token(token)
                if payload and payload.get("sub"):
                    client_id = f"user_{payload.get('sub')}"
            except Exception:
                pass

        key = f"ratelimit:{self.scope}:{client_id}"
        current_time = time.time()

        # Try Redis sliding window counter
        try:
            pipeline = redis_client.pipeline()
            pipeline.zremrangebyscore(key, 0, current_time - self.window_seconds)
            pipeline.zadd(key, {str(current_time): current_time})
            pipeline.zcard(key)
            pipeline.expire(key, self.window_seconds + 5)
            results = pipeline.execute()
            count = results[2]

            if count > self.requests_limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded for {self.scope}. Limit: {self.requests_limit} requests / {self.window_seconds}s. Please wait before retrying.",
                    headers={"Retry-After": str(self.window_seconds)}
                )
        except HTTPException:
            raise
        except Exception:
            # Fallback to local memory sliding window
            timestamps = self.memory_store.get(key, [])
            cutoff = current_time - self.window_seconds
            timestamps = [t for t in timestamps if t > cutoff]
            if len(timestamps) >= self.requests_limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded for {self.scope}. Please wait before retrying."
                )
            timestamps.append(current_time)
            self.memory_store[key] = timestamps
