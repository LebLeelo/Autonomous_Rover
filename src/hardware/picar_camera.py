"""Le seul module du projet qui accède à la caméra (picamera2).

On n'utilise PAS le Camera d'Adeept (camera_opencv.py) pour la perception :
  1. BaseCamera.get_frame() rend du JPEG encodé (perte + coût de décodage) ;
  2. son CVThread.findColor() pilote les servos caméra en pleine détection.
On garde les fichiers Adeept intacts pour leur web UI, et on lit Picamera2
en BGR numpy directement ici.
"""
import time

import numpy as np
from picamera2 import Picamera2
import libcamera

from src.common.errors import CameraError
from src.common.types import Frame


class PicarCamera:
    def __init__(self, width=640, height=480, hflip=False, vflip=False,
                 min_fps=5.0):
        self.width = width
        self.height = height
        self.min_fps = min_fps
        self._fps_ema = 0.0
        self._last_ts = 0.0
        self._n_frames = 0

        try:
            self._cam = Picamera2()
            cfg = self._cam.create_preview_configuration(
                main={"size": (width, height), "format": "RGB888"},
                transform=libcamera.Transform(hflip=hflip, vflip=vflip),
            )
            self._cam.configure(cfg)
            self._cam.start()
        except Exception as exc:
            raise CameraError(f"camera init failed: {exc}") from exc

        for _ in range(10):              # warm-up : premières frames mal exposées
            self._raw_read()

    def _raw_read(self) -> np.ndarray:
        try:
            arr = self._cam.capture_array()
        except Exception as exc:
            raise CameraError(f"capture failed: {exc}") from exc
        if arr is None or arr.size == 0:
            raise CameraError("empty frame")
        # Même convention que camera_opencv.py : le buffer RGB888 arrive
        # directement exploitable comme BGR par OpenCV.
        return arr[:, :, :3]

    def read(self) -> Frame:
        img = np.ascontiguousarray(self._raw_read())
        ts = time.time()
        if self._last_ts:
            inst = 1.0 / max(ts - self._last_ts, 1e-6)
            self._fps_ema = 0.8 * self._fps_ema + 0.2 * inst
        self._last_ts = ts
        self._n_frames += 1
        return Frame(image=img, timestamp=ts)

    @property
    def fps(self) -> float:
        return self._fps_ema

    def is_healthy(self) -> bool:
        """Pour le HealthMonitor (Jour 3) : FPS acceptable après warm-up."""
        return self._n_frames < 20 or self._fps_ema >= self.min_fps

    def release(self):
        try:
            self._cam.stop()
        except Exception:
            pass