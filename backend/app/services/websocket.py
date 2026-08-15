import json
import asyncio
from fastapi import WebSocket
from typing import Dict, List, Set
import redis.asyncio as aioredis
from ..config import settings

class WebSocketManager:
    def __init__(self):
        # Maps submission_id -> set of active WebSockets
        self.submission_subscribers: Dict[str, Set[WebSocket]] = {}
        
        # Maps problem_id (room_id) -> list of active WebSockets
        self.collaboration_rooms: Dict[str, Set[WebSocket]] = {}
        
        # Redis listener task reference
        self.listener_task = None

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

    # --- COLLABORATIVE PAIR PROGRAMMING (Yjs / Real-time Sync) ---
    async def join_room(self, room_id: str, websocket: WebSocket):
        if room_id not in self.collaboration_rooms:
            self.collaboration_rooms[room_id] = set()
        self.collaboration_rooms[room_id].add(websocket)
        print(f"[*] Client joined room: {room_id}. Total peers: {len(self.collaboration_rooms[room_id])}")

    async def leave_room(self, room_id: str, websocket: WebSocket):
        if room_id in self.collaboration_rooms:
            self.collaboration_rooms[room_id].discard(websocket)
            print(f"[*] Client left room: {room_id}. Total peers remaining: {len(self.collaboration_rooms[room_id])}")
            if not self.collaboration_rooms[room_id]:
                del self.collaboration_rooms[room_id]

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
