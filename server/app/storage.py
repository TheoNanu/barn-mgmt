import os
import threading
from pathlib import Path
from typing import Union

from pydantic import BaseModel

from .models import Camera, CameraBase

# The uploaded map and the cameras JSON file live here (created on startup).
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class CameraFile(BaseModel):
    """Contents of the cameras JSON file."""

    # Tracked separately so ids of deleted cameras are never reused.
    next_id: int = 1
    cameras: list[Camera] = []


class CameraStore:
    """Cameras persisted in a JSON file.

    Every operation reads and rewrites the whole file under a lock, because
    FastAPI runs sync endpoints concurrently in a thread pool.
    """

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def all(self) -> list[Camera]:
        with self._lock:
            return self._read().cameras

    def create(self, fields: CameraBase) -> Camera:
        with self._lock:
            data = self._read()
            camera = Camera(id=data.next_id, **fields.model_dump())
            data.cameras.append(camera)
            data.next_id += 1
            self._write(data)
            return camera

    def update(self, camera_id: int, fields: CameraBase) -> Camera | None:
        with self._lock:
            data = self._read()
            for i, camera in enumerate(data.cameras):
                if camera.id == camera_id:
                    data.cameras[i] = Camera(id=camera_id, **fields.model_dump())
                    self._write(data)
                    return data.cameras[i]
            return None

    def delete(self, camera_id: int) -> bool:
        with self._lock:
            data = self._read()
            remaining = [c for c in data.cameras if c.id != camera_id]
            if len(remaining) == len(data.cameras):
                return False
            data.cameras = remaining
            self._write(data)
            return True

    def _read(self) -> CameraFile:
        if not self.path.exists():
            return CameraFile()
        return CameraFile.model_validate_json(self.path.read_text(encoding="utf-8"))

    def _write(self, data: CameraFile) -> None:
        # Write a temporary file and swap it in, so a crash mid-write can't corrupt the data.
        tmp_path = self.path.with_name(self.path.name + ".tmp")
        tmp_path.write_text(data.model_dump_json(indent=2), encoding="utf-8")
        os.replace(tmp_path, self.path)

    def get(self, camera_id: int) -> Union[Camera, None]:
        with self._lock:
            return next((c for c in self._read().cameras if c.id == camera_id), None)



camera_store = CameraStore(DATA_DIR / "cameras.json")
