import unittest

from src.manipulation.manipulator import AdeeptManipulator


class FakeServoController:
    def __init__(self):
        self.calls = []
        self.angles = {2: 90, 4: 90}

    def returnServoAngle(self, channel):
        return self.angles[channel]

    def singleServo(self, channel, direction, speed):
        self.calls.append(("move", channel, direction, speed))

    def stopWiggle(self):
        self.calls.append(("stop",))


class ManipulatorTests(unittest.TestCase):
    def test_grasp_sequence_uses_arm_and_gripper_channels(self):
        controller = FakeServoController()
        manipulator = AdeeptManipulator(
            servo_controller=controller,
            target_detector=object(),
            settle_s=0,
            sleep_fn=lambda _: None,
        )
        self.assertTrue(manipulator.self_test())
        manipulator.perform_action()
        self.assertEqual(
            controller.calls,
            [
                ("move", 4, 1, 3), ("stop",),
                ("move", 2, -1, 3), ("stop",),
                ("move", 4, -1, 3), ("stop",),
                ("move", 2, 1, 3), ("stop",),
            ],
        )

    def test_action_verification_requires_target_to_disappear(self):
        class Detector:
            def detect(self, frame):
                return type("Detection", (), {"found": False})()

        class Robot:
            def get_camera_frame(self):
                return object()

        arm = AdeeptManipulator(
            servo_controller=FakeServoController(),
            target_detector=Detector(),
            verify_frames=2,
        )
        self.assertTrue(arm.verify_action(Robot()))


if __name__ == "__main__":
    unittest.main()