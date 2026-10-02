# src/hardware/robot_interface.py
from abc import ABC, abstractmethod
from typing import Optional

from src.common.types import Frame

class RobotInterface(ABC):

    @abstractmethod
    def move(self, v: float, omega: float) -> None:
        """v ∈ [-1,1] vitesse, omega ∈ [-1,1] rotation."""

    @abstractmethod
    def stop(self) -> None:
        """Arrêt immédiat."""

    @abstractmethod
    def get_camera_frame(self) -> Frame:
        """Return a captured frame with its capture timestamp."""

    @abstractmethod
    def get_battery(self) -> Optional[float]:
        """Return battery fraction (0..1), or None when telemetry is unavailable."""