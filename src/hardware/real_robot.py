# src/hardware/real_robot.py
import Move                                    # code Adeept → pins 26, 21, 27, 18...
from src.hardware.robot_interface import RobotInterface
from src.hardware.picar_camera import PicarCamera

class RealRobot(RobotInterface):
    def __init__(self):
        self._camera = CameraStream()

    def move(self, v: float, omega: float):
        speed = int(abs(v) * 100)
        direction = 'forward' if v >= 0 else 'backward'
        turn = 'no' if abs(omega) < 0.05 else ('left' if omega > 0 else 'right')
        radius = max(0.2, min(1.0, abs(omega)))
        Move.move(speed, direction, turn, radius)

    def stop(self):
        Move.motorStop()

    def get_camera_frame(self):
        return self._camera.read()

    def get_battery(self):
        return self._adc_level / 100.0