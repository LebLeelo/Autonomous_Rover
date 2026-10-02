from typing import Callable, Optional

from src.hardware.robot_interface import RobotInterface


class RealRobot(RobotInterface):
    def __init__(self, drive=None, camera=None,
                 battery_reader: Optional[Callable[[], float]] = None):
        if drive is None:
            import Move as drive
        if camera is None:
            from src.hardware.picar_camera import PicarCamera
            camera = PicarCamera()
        self._drive = drive
        self._camera = camera
        self._battery_reader = battery_reader

    def move(self, v: float, omega: float):
        if abs(v) < 0.01 and abs(omega) < 0.01:
            self.stop()
            return

        if abs(v) < 0.01:
            direction = 'no'
            speed = int(abs(omega) * 100)
        else:
            direction = 'forward' if v > 0 else 'backward'
            speed = int(abs(v) * 100)

        turn = 'no' if abs(omega) < 0.05 else ('left' if omega > 0 else 'right')
        radius = max(0.2, min(1.0, 1.0 - abs(omega) * 0.8))
        self._drive.move(speed, direction, turn, radius)

    def stop(self):
        self._drive.motorStop()

    def get_camera_frame(self):
        return self._camera.read()

    def get_battery(self):
        if self._battery_reader is None:
            return None
        return self._battery_reader()