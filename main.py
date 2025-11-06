# main.py
import time
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse, JSONResponse
from vision_detect import get_latest, get_mjpeg_frame_bytes
import db

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Simple connection manager for broadcasting to websockets
class ConnectionManager:
    def __init__(self):
        self.active: set[WebSocket] = set()
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)
    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)
    async def broadcast(self, message: dict):
        to_remove = []
        for ws in list(self.active):
            try:
                await ws.send_json(message)
            except Exception:
                to_remove.append(ws)
        for ws in to_remove:
            self.disconnect(ws)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    # init DB
    await db.init_db()
    # start a background broadcaster that pushes latest every second
    asyncio.create_task(broadcaster_task())

async def broadcaster_task():
    while True:
        data = get_latest()
        payload = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "count": data["count"],
            "tracks": data["tracks"]
        }
        await manager.broadcast(payload)
        await asyncio.sleep(1.0)

@app.get("/")
async def home():
    return {"status": "Phone Detection API running"}

@app.get("/latest")
async def latest():
    data = get_latest()
    return JSONResponse({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "phones_detected": data["count"],
        "tracks": data["tracks"]
    })

@app.get("/stream")
def stream():
    def gen():
        boundary = b"--frame\r\n"
        while True:
            frame = get_mjpeg_frame_bytes(draw_boxes=True)
            yield boundary + b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
    return Response(gen(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # keep connection open; client may send ping messages
            _ = await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
