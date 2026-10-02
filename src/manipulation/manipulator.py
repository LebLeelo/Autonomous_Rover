import time
from abc import ABC, abstractmethod


class Manipulator(ABC):
    @abstractmethod
    def self_test(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def perform_action(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def verify_action(self, robot) -> bool:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError


class AdeeptManipulator(Manipulator):
    """Timed grasp sequence using Adeept servo channels 2 and 4."""

    def __init__(self, servo_controller=None, target_detector=None,
                 settle_s=0.4, verify_frames=3, sleep_fn=time.sleep):
        if servo_controller is None:
            import RPIservo
            servo_controller = RPIservo.ServoCtrl(daemon=True)
            servo_controller.moveInit()
            servo_controller.start()
        if target_detector is None:
            from src.perception.target_detector import ColorTargetDetector
            target_detector = ColorTargetDetector()
        self._servos = servo_controller
        self._target_detector = target_detector
        self._settle_s = settle_s
        self._verify_frames = verify_frames
        self._sleep = sleep_fn

    def self_test(self) -> bool:
        read_angle = getattr(self._servos, "returnServoAngle", None)
        if read_angle is None:
            return False
        try:
            return all(0 <= read_angle(channel) <= 180 for channel in (2, 4))
        except Exception:
            return False

    def perform_action(self) -> None:
        self._move_servo(4, 1, self._settle_s)
        self._move_servo(2, -1, self._settle_s)
        self._move_servo(4, -1, self._settle_s)
        self._move_servo(2, 1, self._settle_s)

    def verify_action(self, robot) -> bool:
        for _ in range(self._verify_frames):
            detection = self._target_detector.detect(robot.get_camera_frame())
            if detection.found:
                return False
        return True

    def stop(self) -> None:
        self._servos.stopWiggle()

    def _move_servo(self, channel, direction, duration_s):
        self._servos.singleServo(channel, direction, 3)
        try:
            self._sleep(duration_s)
        finally:
            self._servos.stopWiggle()