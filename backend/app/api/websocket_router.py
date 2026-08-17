from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.websocket import websocket_manager

router = APIRouter(prefix="/ws", tags=["websockets"])

@router.websocket("/submissions/{submission_id}")
async def submission_websocket_endpoint(websocket: WebSocket, submission_id: str):
    await websocket.accept()
    await websocket_manager.subscribe_submission(submission_id, websocket)
    
    try:
        # Keep connection open and wait for client to disconnect or send pings
        while True:
            # We don't expect much client data, but we must read to detect closures
            data = await websocket.receive_text()
            # If the client wants to ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.unsubscribe_submission(submission_id, websocket)

@router.websocket("/collaboration/{problem_id}")
async def collaboration_websocket_endpoint(websocket: WebSocket, problem_id: str):
    await websocket.accept()
    await websocket_manager.join_room(problem_id, websocket)
    
    try:
        while True:
            # Receive sync data/cursors/chat from this peer
            message = await websocket.receive_text()
            # Process Redis state persistence and broadcast
            await websocket_manager.handle_room_message(problem_id, websocket, message)
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.leave_room(problem_id, websocket)

@router.get("/room/{room_code}")
async def get_collab_room_info(room_code: str):
    """
    Returns collaboration room metadata from Redis if the session is alive.
    """
    try:
        r = await websocket_manager.get_redis()
        room_key = f"collab:room:{room_code.upper()}"
        data_str = await r.get(room_key)
        if data_str:
            import json
            data = json.loads(data_str)
            return {"exists": True, **data}
    except Exception as e:
        print(f"[!] Error fetching room info: {e}")
    return {"exists": False}
