"""Composant Perception de l'architecture (§5.1).

Fusionne deux sources (caméra + ultrason) en un PerceptionResult unique,
consommé par la Navigation. C'est LA frontière perception → décision :
au-delà de ce point, plus personne ne touche une image brute.
"""
import time

from src.common.types import Frame, PerceptionResult
from src.perception.obstacle_detector import ObstacleDetector
from src.perception.target_detector import ColorTargetDetector


class PerceptionService:
    def __init__(self,
                 target_detector: ColorTargetDetector = None,
                 obstacle_detector: ObstacleDetector = None):
        self.target = target_detector or ColorTargetDetector()
        self.obstacle = obstacle_detector or ObstacleDetector()

    def process(self, frame: Frame, front_distance_m) -> PerceptionResult:
        """front_distance_m : lecture ultrason en mètres, ou None si indisponible."""
        t0 = time.perf_counter()
        detection = self.target.detect(frame)
        obstacle = self.obstacle.assess(front_distance_m)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return PerceptionResult(target=detection, obstacle=obstacle,
                                latency_ms=latency_ms)