import threading
from collections import Counter
from contextlib import contextmanager

import cv2

# Seconds to wait before reconnecting when the stream can't be opened or drops.
RECONNECT_DELAY = 2


class IPCamera:
    """Reads frames from a camera stream in a background thread, keeping only the latest.

    Reading continuously, rather than only when a frame is needed, stops OpenCV from
    buffering a backlog of old frames, which would make the video lag further and
    further behind. If the stream can't be opened or drops, it keeps reconnecting.
    """

    def __init__(self, stream_url: str):
        self.stream_url = stream_url
        # (frame_id, frame): frame_id grows with every new frame and is 0 until the first.
        # Replaced as a whole, so readers never see a mismatched pair.
        self._latest = (0, None)
        self._stopped = threading.Event()
        # Daemon, so a thread stuck connecting to a camera can't keep the server from exiting.
        self._thread = threading.Thread(target=self._read_frames, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        # Don't wait for the thread: it may be blocked connecting or reading for a while,
        # and it exits on its own once it sees the flag.
        self._stopped.set()

    def latest_frame(self):
        """Return (frame_id, frame) for the newest frame."""
        return self._latest

    def _read_frames(self) -> None:
        while not self._stopped.is_set():
            capture = cv2.VideoCapture(self.stream_url)
            while not self._stopped.is_set():
                ok, frame = capture.read()
                if not ok:
                    break
                self._latest = (self._latest[0] + 1, frame)
            capture.release()
            self._stopped.wait(RECONNECT_DELAY)


class CameraStreams:
    """Shares one IPCamera per stream URL between everyone using it (viewers, later algorithms).

    The stream is opened when the first user subscribes and stopped when the last one
    leaves, so the server never holds more than one connection to a camera.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._cameras: dict[str, IPCamera] = {}
        self._subscribers: Counter[str] = Counter()

    @contextmanager
    def subscribe(self, stream_url: str):
        with self._lock:
            camera = self._cameras.get(stream_url)
            if camera is None:
                camera = self._cameras[stream_url] = IPCamera(stream_url)
                camera.start()
            self._subscribers[stream_url] += 1
        try:
            yield camera
        finally:
            with self._lock:
                self._subscribers[stream_url] -= 1
                if not self._subscribers[stream_url]:
                    del self._subscribers[stream_url], self._cameras[stream_url]
                    camera.stop()


camera_streams = CameraStreams()
