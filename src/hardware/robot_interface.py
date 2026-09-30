# src/hardware/robot_interface.py
from abc import ABC, abstractmethod

class RobotInterface(ABC):

    @abstractmethod
    def move(self, v: float, omega: float) -> None:
        """v ∈ [-1,1] vitesse, omega ∈ [-1,1] rotation."""

    @abstractmethod
    def stop(self) -> None:
        """Arrêt immédiat."""

    @abstractmethod
    def get_camera_frame(self):
        """Retourne une frame (numpy array)."""

    @abstractmethod
    def get_battery(self) -> float:
        """Retourne 0.0–1.0."""