"""Transforme une mesure ultrason en information d'obstacle abstraite.

Pure logic : la lecture est INJECTÉE (read_distance_m est ailleurs),
donc testable sans hardware. Range check §22 : donnée hors bornes →
invalide, on ne décide JAMAIS sur une mesure rejetée.
"""
from src.common import config
from src.common.types import Obstacle


class ObstacleDetector:
    def __init__(self,
                 stop_m=config.OBSTACLE_STOP_M,
                 warn_m=config.OBSTACLE_WARN_M,
                 min_valid=config.ULTRASONIC_MIN_VALID_M,
                 max_valid=config.ULTRASONIC_MAX_VALID_M):
        self.stop_m = stop_m
        self.warn_m = warn_m
        self.min_valid = min_valid
        self.max_valid = max_valid

    def assess(self, distance_m) -> Obstacle:
        if distance_m is None or not (self.min_valid <= distance_m <= self.max_valid):
            return Obstacle(valid=False, detected=False, distance_m=None)
        return Obstacle(
            valid=True,
            detected=distance_m <= self.warn_m,
            distance_m=distance_m,
        )

    def is_blocking(self, obs: Obstacle) -> bool:
        """Utilisé par la Navigation (Jour 2) : doit-on s'arrêter ?"""
        return obs.valid and obs.distance_m <= self.stop_m