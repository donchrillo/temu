"""
WebSocket Router - Live Log Streaming

Enthält den WebSocket-Handler für Live-Job-Updates.
"""

import asyncio
from typing import List
from fastapi import APIRouter, WebSocket
from fastapi.encoders import jsonable_encoder
from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedOK, ConnectionClosed

from modules.shared import app_logger


def get_websocket_router(get_scheduler_func):
    """
    Erstellt den WebSocket Router.
    
    Args:
        get_scheduler_func: callable, gibt den Scheduler zurück
    """
    
    router = APIRouter()
    
    connected_clients: List[WebSocket] = []
    
    @router.websocket("/ws/logs")
    async def websocket_logs(websocket: WebSocket):
        """WebSocket für Live-Log-Streaming"""
        await websocket.accept()
        connected_clients.append(websocket)

        try:
            while True:
                await asyncio.sleep(2)
                scheduler = get_scheduler_func()
                if scheduler:
                    jobs = scheduler.get_all_jobs()
                    jobs_serializable = jsonable_encoder(jobs)
                    await websocket.send_json({"type": "jobs_update", "data": jobs_serializable})

        except Exception as e:
            if isinstance(e, (WebSocketDisconnect, ConnectionClosedOK, ConnectionClosed)):
                return
            app_logger.error(f"WebSocket Fehler: {e}", exc_info=True)

        finally:
            if websocket in connected_clients:
                connected_clients.remove(websocket)

    return router
