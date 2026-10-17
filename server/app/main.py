import asyncio
import shutil
import time
from contextlib import asynccontextmanager
from pathlib import Path

import cv2
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.exceptions import WebSocketException
from starlette.websockets import WebSocket, WebSocketDisconnect

from .camera.ip_camera import camera_streams
from .models import Camera, CameraBase
from .storage import DATA_DIR, camera_store

# Accepted content types for the barn map, mapped to the file extension used on disk.
MAP_IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

# Maximum frame rate sent to a live view.
STREAM_FPS = 15
# Seconds without a new frame (wrong URL, camera offline) before a live view is closed.
STREAM_TIMEOUT = 10


@asynccontextmanager
async def lifespan(app: FastAPI):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Barn Management", lifespan=lifespan)


# --- Barn map -----------------------------------------------------------------


def find_map_file() -> Path | None:
    return next(DATA_DIR.glob("map.*"), None)


def map_info() -> dict:
    path = find_map_file()
    if path is None:
        return {"image_url": None}
    # The modification time acts as a cache buster, so browsers reload a replaced map.
    return {"image_url": f"/api/map/image?v={path.stat().st_mtime_ns}"}


@app.get("/api/map")
def get_map():
    return map_info()


@app.put("/api/map")
def upload_map(file: UploadFile):
    extension = MAP_IMAGE_TYPES.get(file.content_type)
    if extension is None:
        raise HTTPException(415, "The map must be a PNG, JPEG, WebP or GIF image")

    path = DATA_DIR / f"map{extension}"
    with path.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    for old_file in DATA_DIR.glob("map.*"):
        if old_file != path:
            old_file.unlink()
    return map_info()


@app.get("/api/map/image")
def get_map_image():
    path = find_map_file()
    if path is None:
        raise HTTPException(404, "No map has been uploaded yet")
    return FileResponse(path)


# --- Cameras ------------------------------------------------------------------


@app.get("/api/cameras", response_model=list[Camera])
def list_cameras():
    return camera_store.all()


@app.post("/api/cameras", response_model=Camera, status_code=201)
def create_camera(data: CameraBase):
    return camera_store.create(data)


@app.put("/api/cameras/{camera_id}", response_model=Camera)
def update_camera(camera_id: int, data: CameraBase):
    camera = camera_store.update(camera_id, data)
    if camera is None:
        raise HTTPException(404, "Camera not found")
    return camera


@app.delete("/api/cameras/{camera_id}", status_code=204)
def delete_camera(camera_id: int):
    if not camera_store.delete(camera_id):
        raise HTTPException(404, "Camera not found")


def encode_jpeg(frame) -> bytes:
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    return buffer.tobytes()


@app.websocket("/api/cameras/{camera_id}/stream")
async def camera_stream_websocket(websocket: WebSocket, camera_id: int):
    """Live view: sends the camera's newest frame as a binary JPEG message, up to STREAM_FPS."""
    camera = camera_store.get(camera_id)
    if camera is None:
        raise WebSocketException(code=1008, reason="Camera not found")
    await websocket.accept()

    with camera_streams.subscribe(camera.stream_url) as ip_camera:
        sent_frame_id = 0
        last_new_frame_at = time.monotonic()
        try:
            while True:
                frame_id, frame = ip_camera.latest_frame()
                if frame_id != sent_frame_id:
                    sent_frame_id = frame_id
                    last_new_frame_at = time.monotonic()
                    # Encoding takes a few ms per frame; keep it off the event loop.
                    await websocket.send_bytes(await asyncio.to_thread(encode_jpeg, frame))
                elif time.monotonic() - last_new_frame_at > STREAM_TIMEOUT:
                    await websocket.close(code=1011, reason="No video from the camera")
                    return
                await asyncio.sleep(1 / STREAM_FPS)
        except WebSocketDisconnect:
            pass
