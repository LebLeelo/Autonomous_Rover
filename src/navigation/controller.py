from dataclasses import dataclass

from src.common import config
from src.common.types import PerceptionResult


@dataclass(frozen=True)
class MotionCommand:
    v: float
    omega: float
    behavior: str


class NavigationController:
    """Reactive navigation from target bearing and front range only."""

    def __init__(self, stop_m=config.OBSTACLE_STOP_M,
                 clear_m=config.OBSTACLE_WARN_M, target_deadband=0.12,
                 approach_distance_m=0.45, forward_speed=0.35,
                 turn_speed=0.45):
        self.stop_m = stop_m
        self.clear_m = clear_m
        self.target_deadband = target_deadband
        self.approach_distance_m = approach_distance_m
        self.forward_speed = forward_speed
        self.turn_speed = turn_speed
        self._avoiding = False

    def compute(self, perception: PerceptionResult) -> MotionCommand:
        obstacle = perception.obstacle
        if not obstacle.valid or obstacle.distance_m is None:
            return MotionCommand(0.0, 0.0, "SENSOR_STOP")

        if obstacle.distance_m <= self.stop_m:
            self._avoiding = True
        elif self._avoiding and obstacle.distance_m > self.clear_m:
            self._avoiding = False

        if self._avoiding:
            return MotionCommand(0.0, -self.turn_speed, "AVOID_OBSTACLE")

        target = perception.target
        if not target.found:
            return MotionCommand(0.0, self.turn_speed * 0.6, "SEARCH_TARGET")

        if target.x < -self.target_deadband:
            return MotionCommand(0.0, self.turn_speed, "ALIGN_TARGET")
        if target.x > self.target_deadband:
            return MotionCommand(0.0, -self.turn_speed, "ALIGN_TARGET")

        if (target.distance_m is not None
                and target.distance_m <= self.approach_distance_m):
            return MotionCommand(0.0, 0.0, "TARGET_REACHED")

        return MotionCommand(self.forward_speed, 0.0, "APPROACH_TARGET")