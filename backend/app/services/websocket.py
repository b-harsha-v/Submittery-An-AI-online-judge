import json
import asyncio
import time
from fastapi import WebSocket
from typing import Dict, List, Set, Optional
import redis.asyncio as aioredis
from ..config import settings

class WebSocketManager:
    def __init__(self):
        # Maps submission_id -> set of active WebSockets
        self.submission_subscribers: Dict[str, Set[WebSocket]] = {}
        
        # Maps problem_id (room_id) -> list of active WebSockets
        self.collaboration_rooms: Dict[str, Set[WebSocket]] = {}
        
        # Async Redis client for room caching
        self.async_redis: Optional[aioredis.Redis] = None
        
        # Redis listener task reference
        self.listener_task = None

    async def get_redis(self) -> aioredis.Redis:
        if self.async_redis is None:
            self.async_redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self.async_redis

    # --- SUBMISSION UPDATES ---
    async def subscribe_submission(self, submission_id: str, websocket: WebSocket):
        if submission_id not in self.submission_subscribers:
            self.submission_subscribers[submission_id] = set()
        self.submission_subscribers[submission_id].add(websocket)

    async def unsubscribe_submission(self, submission_id: str, websocket: WebSocket):
        if submission_id in self.submission_subscribers:
            self.submission_subscribers[submission_id].discard(websocket)
            if not self.submission_subscribers[submission_id]:
                del self.submission_subscribers[submission_id]

    async def broadcast_submission_update(self, submission_id: str, data: dict):
        if submission_id in self.submission_subscribers:
            dead_sockets = set()
            for websocket in self.submission_subscribers[submission_id]:
                try:
                    await websocket.send_json(data)
                except Exception:
                    dead_sockets.add(websocket)
            
            for ws in dead_sockets:
                await self.unsubscribe_submission(submission_id, ws)

    # --- COLLABORATIVE PAIR PROGRAMMING (Redis-backed session persistence) ---
    async def join_room(self, room_id: str, websocket: WebSocket):
        room_id = room_id.strip().upper()
        if room_id not in self.collaboration_rooms:
            self.collaboration_rooms[room_id] = set()
        self.collaboration_rooms[room_id].add(websocket)
        print(f"[*] Client joined room: {room_id}. Total active connections: {len(self.collaboration_rooms[room_id])}")

        # Check Redis for existing room state to immediately hydrate this peer
        try:
            r = await self.get_redis()
            room_key = f"collab:room:{room_id}"
            room_data_str = await r.get(room_key)
            if room_data_str:
                room_data = json.loads(room_data_str)
                # Send problem sync to newly connected client immediately
                slug = room_data.get("problem_slug")
                if slug:
                    await websocket.send_text(json.dumps({
                        "type": "sync-problem",
                        "slug": slug
                    }))
                # Send latest cached code if present
                cached_code = room_data.get("current_code")
                if cached_code is not None and cached_code != "":
                    await websocket.send_text(json.dumps({
                        "type": "sync-code",
                        "code": cached_code
                    }))
        except Exception as e:
            print(f"[!] Error hydrating room state from Redis: {e}")

    async def leave_room(self, room_id: str, websocket: WebSocket):
        room_id = room_id.strip().upper()
        if room_id in self.collaboration_rooms:
            self.collaboration_rooms[room_id].discard(websocket)
            print(f"[*] Client left room: {room_id}. Total peers remaining: {len(self.collaboration_rooms[room_id])}")
            if not self.collaboration_rooms[room_id]:
                del self.collaboration_rooms[room_id]

    async def handle_room_message(self, room_id: str, sender: WebSocket, raw_message: str):
        """
        Parses room message, updates Redis state if problem or code changed,
        and broadcasts to all other peers in the room.
        """
        room_id = room_id.strip().upper()
        try:
            data = json.loads(raw_message)
            msg_type = data.get("type")
            r = await self.get_redis()
            room_key = f"collab:room:{room_id}"

            # Save initial room metadata (DO NOT overwrite existing written code if alive in Redis!)
            if msg_type == "init-room":
                existing = await r.get(room_key)
                if existing:
                    room_data = json.loads(existing)
                    # If Redis already had code, keep it! Only use starter if empty
                    if not room_data.get("current_code") and data.get("code"):
                        room_data["current_code"] = data.get("code")
                    if data.get("slug"):
                        room_data["problem_slug"] = data.get("slug")
                    room_data["updated_at"] = time.time()
                else:
                    room_data = {
                        "room_code": room_id,
                        "problem_slug": data.get("slug"),
                        "current_code": data.get("code", ""),
                        "creator": data.get("user", "Host"),
                        "updated_at": time.time()
                    }
                await r.set(room_key, json.dumps(room_data), ex=7200) # 2 hours TTL
                print(f"[*] Persistent collab room {room_id} saved for problem {room_data.get('problem_slug')}")

            # Update problem slug if changed
            elif msg_type == "sync-problem":
                slug = data.get("slug")
                existing = await r.get(room_key)
                if existing:
                    room_data = json.loads(existing)
                    room_data["problem_slug"] = slug
                    room_data["updated_at"] = time.time()
                else:
                    room_data = {
                        "room_code": room_id,
                        "problem_slug": slug,
                        "current_code": "",
                        "updated_at": time.time()
                    }
                await r.set(room_key, json.dumps(room_data), ex=7200)

            # Cache latest code modifications
            elif msg_type == "sync-code":
                code = data.get("code")
                if code is not None:
                    existing = await r.get(room_key)
                    if existing:
                        room_data = json.loads(existing)
                        room_data["current_code"] = code
                        room_data["updated_at"] = time.time()
                    else:
                        room_data = {
                            "room_code": room_id,
                            "problem_slug": "",
                            "current_code": code,
                            "updated_at": time.time()
                        }
                    await r.set(room_key, json.dumps(room_data), ex=7200)

            # Request sync from Redis
            elif msg_type == "request-sync":
                existing = await r.get(room_key)
                if existing:
                    room_data = json.loads(existing)
                    slug = room_data.get("problem_slug")
                    code = room_data.get("current_code")
                    if slug:
                        await sender.send_text(json.dumps({"type": "sync-problem", "slug": slug}))
                    if code:
                        await sender.send_text(json.dumps({"type": "sync-code", "code": code}))

            # Close room explicitly
            elif msg_type == "close-room":
                await r.delete(room_key)
                print(f"[*] Closed collab room {room_id}")

        except Exception as e:
            print(f"[!] Error processing room message: {e}")

        # Broadcast packet to other room peers
        await self.broadcast_to_room(room_id, sender, raw_message)

    async def broadcast_to_room(self, room_id: str, sender: WebSocket, message: str):
        """
        Broadcasts message to all other connected peers in the same room.
        """
        if room_id in self.collaboration_rooms:
            dead_sockets = set()
            for client in self.collaboration_rooms[room_id]:
                if client != sender:
                    try:
                        # Send text or json payload
                        await client.send_text(message)
                    except Exception:
                        dead_sockets.add(client)
            
            for ws in dead_sockets:
                await self.leave_room(room_id, ws)

    # --- REDIS PUB/SUB BACKGROUND LISTENER ---
    async def start_redis_listener(self):
        """
        Starts the background Redis Pub/Sub subscription task.
        Receives updates from the worker and relays them to WebSockets.
        """
        if self.listener_task is not None:
            return
            
        self.listener_task = asyncio.create_task(self._redis_pubsub_loop())
        print("[*] Redis WebSocket status listener task started.")

    async def stop_redis_listener(self):
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
            self.listener_task = None
            print("[*] Redis WebSocket status listener task stopped.")

    async def _redis_pubsub_loop(self):
        while True:
            try:
                # Open async redis connection
                # Host port 6385 as configured
                async_redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                pubsub = async_redis.pubsub()
                await pubsub.subscribe("submission_status_updates")
                
                print("[*] Subscribed to Redis channel 'submission_status_updates'. Listening...")
                
                while True:
                    # Non-blocking pull with a small timeout
                    msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if msg:
                        data = json.loads(msg["data"])
                        submission_id = data.get("submission_id")
                        if submission_id:
                            await self.broadcast_submission_update(submission_id, data)
                    
                    # Prevent spin locks
                    await asyncio.sleep(0.01)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[!] WebSocket Pub/Sub connection error: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

websocket_manager = WebSocketManager()
