import unittest

from src.common.types import Detection, Obstacle, PerceptionResult
from src.fdir.fault_manager import FaultManager
from src.fdir.health_monitor import FaultCode, FaultInjector
from src.mission.mission_manager import MissionManager
from src.mission.states import MissionOutcome, MissionState
from src.navigation.controller import MotionCommand


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, duration):
        self.now += duration


class FakeRobot:
    def __init__(self):
        self.stops = 0
        self.moves = []
        self.battery = None

    def get_camera_frame(self):
        return object()

    def get_battery(self):
        return self.battery

    def move(self, v, omega):
        self.moves.append((v, omega))

    def stop(self):
        self.stops += 1


class FakeSensor:
    def read_distance_m(self):
        return 1.0


class ScriptedNavigator:
    def __init__(self):
        self.ultrasonic_sensor = FakeSensor()
        self.fault_manager = None
        self.received_robot = None
        self.results = [
            (PerceptionResult(Detection(found=False), Obstacle(valid=True,
                               distance_m=1.0)),
             MotionCommand(0.0, 0.2, "SEARCH_TARGET")),
            (PerceptionResult(Detection(found=True, x=0.0, distance_m=0.8),
                              Obstacle(valid=True, distance_m=1.0)),
             MotionCommand(0.2, 0.0, "APPROACH_TARGET")),
            (PerceptionResult(Detection(found=True, x=0.0, distance_m=0.4),
                              Obstacle(valid=True, distance_m=1.0)),
             MotionCommand(0.0, 0.0, "TARGET_REACHED")),
        ]

    def step(self, robot):
        self.received_robot = robot
        return self.results.pop(0)


class FakeManipulator:
    def __init__(self, verified=True):
        self.verified = verified
        self.actions = 0
        self.stops = 0

    def self_test(self):
        return True

    def perform_action(self):
        self.actions += 1

    def verify_action(self, robot):
        return self.verified

    def stop(self):
        self.stops += 1


class FakeLogger:
    def __init__(self):
        self.transitions = []
        self.messages = []

    def state(self, event):
        self.transitions.append(event)

    def info(self, event):
        self.messages.append(event)

    def warn(self, event):
        pass

    def error(self, event):
        pass


class MissionTests(unittest.TestCase):
    def make_manager(self, *, verified=True, injector=None):
        clock = FakeClock()
        robot = FakeRobot()
        arm = FakeManipulator(verified=verified)
        logger = FakeLogger()
        manager = MissionManager(
            robot=robot,
            navigator=ScriptedNavigator(),
            manipulator=arm,
            fault_manager=FaultManager(logger=logger),
            fault_injector=injector or FaultInjector(),
            loop_period_s=0.1,
            health_period_s=10.0,
            mission_timeout_s=30.0,
            clock=clock,
            sleep_fn=clock.sleep,
            logger=logger,
        )
        return manager, robot, arm

    def test_complete_mission_manipulates_verifies_and_returns(self):
        manager, robot, arm = self.make_manager()
        outcome = manager.run(max_steps=30)
        self.assertEqual(outcome, MissionOutcome.SUCCESS)
        self.assertEqual(manager.state, MissionState.DONE)
        self.assertEqual(arm.actions, 1)
        self.assertTrue(any(v < 0 for v, _ in robot.moves))
        self.assertIs(manager.navigator.received_robot, robot)
        self.assertIn("mission result: SUCCESS", manager.logger.messages)

    def test_failed_action_verification_enters_safe_mode(self):
        manager, robot, arm = self.make_manager(verified=False)
        outcome = manager.run(max_steps=20)
        self.assertEqual(outcome, MissionOutcome.SAFE)
        self.assertEqual(manager.state, MissionState.SAFE_MODE)
        self.assertGreater(robot.stops, 0)
        self.assertGreater(arm.stops, 0)

    def test_injected_motor_fault_enters_safe_before_mission(self):
        injector = FaultInjector()
        injector.inject(FaultCode.MOTOR_FAILURE)
        manager, robot, arm = self.make_manager(injector=injector)
        outcome = manager.run(max_steps=5)
        self.assertEqual(outcome, MissionOutcome.SAFE)
        self.assertEqual(manager.state, MissionState.SAFE_MODE)
        self.assertEqual(arm.actions, 0)
        self.assertGreater(robot.stops, 0)
        self.assertGreater(arm.stops, 0)

    def test_injected_communication_fault_enters_safe_before_mission(self):
        injector = FaultInjector()
        injector.inject(FaultCode.COMMUNICATION_LOSS)
        manager, robot, arm = self.make_manager(injector=injector)
        outcome = manager.run(max_steps=5)
        self.assertEqual(outcome, MissionOutcome.SAFE)
        self.assertEqual(manager.state, MissionState.SAFE_MODE)
        self.assertEqual(arm.actions, 0)
        self.assertGreater(robot.stops, 0)
        self.assertGreater(arm.stops, 0)

    def test_transient_camera_injection_recovers_without_skipping_self_test(self):
        injector = FaultInjector()
        injector.inject(FaultCode.CAMERA_FAILURE)
        manager, _, _ = self.make_manager(injector=injector)
        outcome = manager.run(max_steps=30)
        self.assertEqual(outcome, MissionOutcome.SUCCESS)
        self.assertIn("RECOVERY -> BOOT", manager.logger.transitions)
        self.assertIn("BOOT -> SELF_TEST", manager.logger.transitions)
        self.assertFalse(injector.active)

    def test_low_battery_requests_return_and_aborts_objectives(self):
        injector = FaultInjector()
        injector.inject(FaultCode.BATTERY_LOW)
        manager, _, arm = self.make_manager(injector=injector)
        outcome = manager.run(max_steps=10)
        self.assertEqual(outcome, MissionOutcome.ABORTED)
        self.assertEqual(manager.state, MissionState.DONE)
        self.assertEqual(arm.actions, 0)

    def test_emergency_stop_enters_safe_and_stops_actuators(self):
        manager, robot, arm = self.make_manager()
        manager.step()
        manager.emergency_stop()
        self.assertEqual(manager.outcome, MissionOutcome.SAFE)
        self.assertEqual(manager.state, MissionState.SAFE_MODE)
        self.assertGreater(robot.stops, 0)
        self.assertGreater(arm.stops, 0)


if __name__ == "__main__":
    unittest.main()