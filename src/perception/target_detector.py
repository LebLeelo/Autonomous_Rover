"""Détection de cible par couleur (HSV) — pur, testable sur laptop.

Entrée : Frame (image BGR).
Sortie : Detection ABSTRAITE (x normalisé, distance estimée, confiance).

Distance : modèle du rayon apparent  d = K / r
avec K = CALIB_DISTANCE_M * CALIB_RADIUS_PX (calibré une fois avec
tools/calibrate_color.py). Explicable en entretien : "apparent size is
inversely proportional to distance, so I calibrated one constant K."
"""
import time

import cv2
import numpy as np

from src.common import config
from src.common.types import Detection, Frame


class ColorTargetDetector:
    def __init__(self,
                 hsv_low=config.TARGET_HSV_LOW,
                 hsv_high=config.TARGET_HSV_HIGH,
                 min_area_px=config.TARGET_MIN_AREA_PX,
                 calib_distance_m=config.CALIB_DISTANCE_M,
                 calib_radius_px=config.CALIB_RADIUS_PX,
                 ref_area_px=config.TARGET_REF_AREA_PX):
        self.hsv_low = np.array(hsv_low, dtype=np.uint8)
        self.hsv_high = np.array(hsv_high, dtype=np.uint8)
        self.min_area_px = min_area_px
        self.k = calib_distance_m * calib_radius_px     # K de d = K / r
        self.ref_area_px = ref_area_px

    def detect(self, frame: Frame) -> Detection:
        hsv = cv2.cvtColor(frame.image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.hsv_low, self.hsv_high)
        mask = cv2.erode(mask, None, iterations=2)    # anti-bruit
        mask = cv2.dilate(mask, None, iterations=2)  # consolide la tache

        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)[-2]
        if not cnts:
            return Detection(found=False)

        c = max(cnts, key=cv2.contourArea)
        area = cv2.contourArea(c)
        if area < self.min_area_px:
            return Detection(found=False)

        M = cv2.moments(c)
        if M["m00"] == 0:
            return Detection(found=False)

        (bx, by), radius = cv2.minEnclosingCircle(c)
        h, w = frame.image.shape[:2]

        return Detection(
            found=True,
            x=(M["m10"] / M["m00"]) / w * 2.0 - 1.0,    # -1 = gauche, +1 = droite
            y=(M["m01"] / M["m00"]) / h * 2.0 - 1.0,
            radius_px=radius,
            distance_m=(self.k / radius) if radius > 1.0 else None,
            confidence=min(1.0, area / self.ref_area_px),  # aire saturée → 1.0
        )

    def annotate(self, image: np.ndarray, det: Detection) -> np.ndarray:
        """Uniquement pour les logs / vidéo de démo — jamais pour décider."""
        out = image.copy()
        if det.found:
            h, w = out.shape[:2]
            cx = int((det.x + 1.0) / 2.0 * w)
            cy = int((det.y + 1.0) / 2.0 * h)
            cv2.circle(out, (cx, cy), int(det.radius_px), (0, 255, 0), 2)
            cv2.putText(out,
                        f"x={det.x:+.2f} d={det.distance_m:.2f}m conf={det.confidence:.2f}",
                        (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)
        else:
            cv2.putText(out, "TARGET: none", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 1)
        return out