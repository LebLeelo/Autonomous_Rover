import unittest

from src.common.errors import CameraError
from src.common.types import Detection, Obstacle, PerceptionResult
from src.hardware.real_robot import RealRobot
from src.hardware.ultrasonic import UltrasonicSensor
from src.fdir.fault_manager import FaultManager
from src.navigation.controller import NavigationController
from src.navigation.navigator import Navigator
from src.perception.obstacle_detector import ObstacleDetector


def result(target=None, obstacle=None):
    return PerceptionResult(target or Detection(), obstacle or Obstacle(valid=True,
                            distance_m=1.0), latency_ms=0.0)


class FakeDrive:
    def __init__(self):
        self.commands = []
        self.stops = 0

    def move(self, *args):
        self.commands.append(args)

    def motorStop(self):
        self.stops += 1


class FakeCamera:
    def read(self):
        return "frame"


class NavigationTests(unittest.TestCase):
    def test_target_bearing_maps_to_turn_direction(self):
        controller = NavigationController()
        command = controller.compute(result(Detection(found=True, x=-0.5)))
        self.assertEqual(command.behavior, "ALIGN_TARGET")
        self.assertGreater(command.omega, 0)

    def test_obstacle_turns_until_clear_distance(self):
        controller = NavigationController()
        blocked = result(Detection(found=True), Obstacle(valid=True, distance_m=0.2))
        clear_but_hysteresis = result(Detection(found=True), Obstacle(valid=True,
                                      distance_m=0.5))
        clear = result(Detection(found=True), Obstacle(valid=True, distance_m=0.7))
        self.assertEqual(controller.compute(blocked).behavior, "AVOID_OBSTACLE")
        self.assertEqual(controller.compute(clear_but_hysteresis).behavior,
                         "AVOID_OBSTACLE")
        self.assertEqual(controller.compute(clear).behavior, "APPROACH_TARGET")

    def test_obstacle_detector_classifies_front_range(self):
        detector = ObstacleDetector()
        self.assertTrue(detector.assess(0.4).detected)
        self.assertFalse(detector.assess(None).valid)
        self.assertTrue(detector.is_blocking(detector.assess(0.2)))

    def test_invalid_obstacle_reading_stops(self):
        command = NavigationController().compute(result(Detection(found=True),
                                                       Obstacle(valid=False)))
        self.assertEqual(command.behavior, "SENSOR_STOP")
        self.assertEqual((command.v, command.omega), (0.0, 0.0))

    def test_real_robot_translates_turn_and_stop_to_adeept_api(self):
        drive = FakeDrive()
        robot = RealRobot(drive=drive, camera=FakeCamera())
        robot.move(0.0, -0.5)
        robot.move(0.35, 0.0)
        robot.stop()
        self.assertEqual(drive.commands[0][1:3], ("no", "right"))
        self.assertEqual(drive.commands[1][1:3], ("forward", "no"))
        self.assertEqual(drive.stops, 1)

    def test_adeept_ultrasonic_centimeters_convert_to_meters(self):
        class Driver:
            @staticmethod
            def checkdist():
                return 42.5

        self.assertAlmostEqual(UltrasonicSensor(Driver()).read_distance_m(), 0.425)

    def test_navigator_stops_when_safe_state_is_latched(self):
        class LatchedFaultManager:
            safe_latched = True

        drive = FakeDrive()
        robot = RealRobot(drive=drive, camera=FakeCamera())
        class UnusedPerception:
            pass

        _, command = Navigator(perception=UnusedPerception(),
                               fault_manager=LatchedFaultManager()).step(robot)
        self.assertEqual(command.behavior, "SAFE")
        self.assertEqual(drive.stops, 1)

    def test_camera_retry_is_verified_before_navigation_resumes(self):
        class IntermittentCamera:
            def __init__(self):
                self.calls = 0

            def read(self):
                self.calls += 1
                if self.calls == 1:
                    raise CameraError("temporary capture failure")
                return object()

        class FakePerception:
            def process(self, frame, distance):
                self.frame = frame
                return result(Detection(found=True),
                              Obstacle(valid=True, distance_m=1.0))

        drive = FakeDrive()
        camera = IntermittentCamera()
        robot = RealRobot(drive=drive, camera=camera)
        perception = FakePerception()
        navigator = Navigator(perception=perception, fault_manager=FaultManager())
        _, command = navigator.step(robot, front_distance_m=1.0)
        self.assertEqual(camera.calls, 2)
        self.assertIsNotNone(perception.frame)
        self.assertEqual(command.behavior, "APPROACH_TARGET")


if __name__ == "__main__":
    unittest.main()