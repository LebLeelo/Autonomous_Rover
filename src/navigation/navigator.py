from src.common.errors import CameraError, UltrasonicError
from src.fdir.fault_manager import FaultManager, RecoveryDecision
from src.fdir.health_monitor import Fault, FaultCode, Severity
from src.navigation.controller import NavigationController


class Navigator:
    """Acquire a perception result, decide, and issue one robot command."""

    def __init__(self, perception=None, controller=None, ultrasonic_sensor=None,
                 fault_manager=None):
        if perception is None:
            from src.perception.perception_service import PerceptionService
            perception = PerceptionService()
        self.perception = perception
        self.controller = controller or NavigationController()
        self.ultrasonic_sensor = ultrasonic_sensor
        self.fault_manager = fault_manager

    def step(self, robot, front_distance_m=None):
        if self.fault_manager is not None and self.fault_manager.safe_latched:
            robot.stop()
            return None, self._safe_command()

        if front_distance_m is None and self.ultrasonic_sensor is not None:
            front_distance_m = self._read_ultrasonic(robot)

        try:
            frame = robot.get_camera_frame()
        except CameraError as exc:
            frame = self._recover_camera(robot, exc)
            if frame is None:
                return None, self._safe_command()

        result = self.perception.process(frame, front_distance_m)
        command = self.controller.compute(result)
        if command.v == 0.0 and command.omega == 0.0:
            robot.stop()
        else:
            robot.move(command.v, command.omega)
        return result, command

    def _read_ultrasonic(self, robot):
        try:
            return self.ultrasonic_sensor.read_distance_m()
        except UltrasonicError as exc:
            fault = Fault(FaultCode.ULTRASONIC_FAILURE, Severity.RECOVERABLE,
                          str(exc))
            if self.fault_manager is None:
                return None
            recovered = []
            decision = self.fault_manager.handle(
                fault, robot,
                retry=lambda: recovered.append(self.ultrasonic_sensor.read_distance_m()),
                verify=lambda: bool(recovered),
            )
            return recovered[-1] if decision == RecoveryDecision.RESUME else None

    def _recover_camera(self, robot, error):
        if self.fault_manager is None:
            robot.stop()
            raise error
        recovered = []
        fault = Fault(FaultCode.CAMERA_FAILURE, Severity.RECOVERABLE,
                      "camera capture failed")
        decision = self.fault_manager.handle(
            fault, robot,
            retry=lambda: recovered.append(robot.get_camera_frame()),
            verify=lambda: bool(recovered) and self._frame_usable(recovered[-1]),
        )
        return recovered[-1] if decision == RecoveryDecision.RESUME else None

    @staticmethod
    def _frame_usable(frame):
        return frame is not None and getattr(frame, "image", frame) is not None

    @staticmethod
    def _safe_command():
        from src.navigation.controller import MotionCommand
        return MotionCommand(0.0, 0.0, "SAFE")