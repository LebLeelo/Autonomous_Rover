import argparse
import time
from dataclasses import dataclass

from src.common.errors import CameraError, UltrasonicError
from src.fdir.fault_manager import FaultManager, HealthState, RecoveryDecision
from src.fdir.health_monitor import (
	Fault,
	FaultCode,
	FaultInjector,
	HealthMonitor,
	Severity,
)
from src.mission.states import MissionOutcome, MissionState, can_transition


@dataclass(frozen=True)
class MotionSegment:
	v: float
	omega: float
	duration_s: float


class MissionManager:
	"""Owns mission state, health decisions, manipulation, and return flow."""

	def __init__(self, robot, navigator, manipulator, health_monitor=None,
				 fault_manager=None, fault_injector=None, telemetry=None,
				 logger=None, loop_period_s=0.05, health_period_s=1.0,
				 mission_timeout_s=180.0, clock=time.monotonic,
				 sleep_fn=time.sleep):
		self.robot = robot
		self.navigator = navigator
		self.manipulator = manipulator
		self.health_monitor = health_monitor or HealthMonitor()
		self.fault_manager = fault_manager or FaultManager(logger=logger)
		self.fault_manager.manipulator = manipulator
		self.fault_injector = fault_injector or FaultInjector()
		self.telemetry = telemetry
		self.logger = logger
		self.loop_period_s = loop_period_s
		self.health_period_s = health_period_s
		self.mission_timeout_s = mission_timeout_s
		self.clock = clock
		self.sleep = sleep_fn
		self.state = MissionState.BOOT
		self.outcome = None
		self._started_at = None
		self._last_health_check = self.clock() - health_period_s
		self._handled_faults = set()
		self._motion_history = []
		self._last_nav_command = None
		self._return_queue = []
		self._return_active = None
		self._return_as_abort = False

		if getattr(self.navigator, "fault_manager", None) is None:
			self.navigator.fault_manager = self.fault_manager

	def run(self, max_steps=None):
		steps = 0
		while self.outcome is None:
			self.step()
			steps += 1
			if self.outcome is not None:
				break
			if max_steps is not None and steps >= max_steps:
				self._handle_fault(Fault(FaultCode.MISSION_TIMEOUT,
										 Severity.CRITICAL,
										 "maximum mission steps reached"))
				break
			self.sleep(self.loop_period_s)
		return self.outcome

	def step(self):
		if self.outcome is not None:
			return self.state
		now = self.clock()
		if self._started_at is None:
			self._started_at = now
		if now - self._started_at >= self.mission_timeout_s:
			self._handle_fault(Fault(FaultCode.MISSION_TIMEOUT,
									 Severity.CRITICAL, "mission timeout"))
			return self.state

		self._poll_health(now)
		if self.outcome is not None:
			return self.state

		if self.state == MissionState.BOOT:
			self._transition(MissionState.SELF_TEST)
		elif self.state == MissionState.SELF_TEST:
			if self._self_test():
				self._transition(MissionState.IDLE)
		elif self.state == MissionState.IDLE:
			self._transition(MissionState.MISSION)
		elif self.state == MissionState.MISSION:
			self._transition(MissionState.NAVIGATE)
		elif self.state in {MissionState.NAVIGATE, MissionState.SEARCH_TARGET,
							MissionState.APPROACH}:
			self._navigation_step()
		elif self.state == MissionState.MANIPULATE:
			self._manipulate()
		elif self.state == MissionState.VERIFY_ACTION:
			self._verify_action()
		elif self.state == MissionState.RETURN_HOME:
			self._return_step()
		return self.state

	def emergency_stop(self):
		self._handle_fault(Fault(FaultCode.EMERGENCY_STOP, Severity.CRITICAL,
								 "operator emergency stop"))

	def _self_test(self):
		try:
			frame = self.robot.get_camera_frame()
			if frame is None or getattr(frame, "image", frame) is None:
				raise CameraError("self-test received an empty frame")
		except CameraError as exc:
			recovered_frames = []

			def retry_camera():
				recovered_frames.append(self.robot.get_camera_frame())

			decision = self._handle_fault(
				Fault(FaultCode.CAMERA_FAILURE, Severity.RECOVERABLE, str(exc)),
				retry=retry_camera,
				verify=lambda: bool(recovered_frames)
				and recovered_frames[-1] is not None
				and getattr(recovered_frames[-1], "image", recovered_frames[-1])
				is not None,
			)
			if decision != RecoveryDecision.RESUME:
				return False

		sensor = getattr(self.navigator, "ultrasonic_sensor", None)
		if sensor is None:
			self._handle_fault(Fault(FaultCode.ULTRASONIC_FAILURE,
									 Severity.CRITICAL,
									 "no ultrasonic sensor configured"))
			return False
		try:
			sensor.read_distance_m()
		except UltrasonicError as exc:
			recovered_distances = []

			def retry_ultrasonic():
				recovered_distances.append(sensor.read_distance_m())

			decision = self._handle_fault(
				Fault(FaultCode.ULTRASONIC_FAILURE, Severity.RECOVERABLE,
					  str(exc)),
				retry=retry_ultrasonic,
				verify=lambda: bool(recovered_distances)
				and recovered_distances[-1] > 0,
			)
			if decision != RecoveryDecision.RESUME:
				return False

		try:
			manipulator_ready = self.manipulator.self_test()
		except Exception as exc:
			manipulator_ready = False
			detail = str(exc)
		else:
			detail = "manipulator self-test failed"
		if not manipulator_ready:
			self._handle_fault(Fault(FaultCode.MANIPULATION_FAILURE,
									 Severity.CRITICAL,
									 detail))
			return False
		return True

	def _poll_health(self, now):
		if now - self._last_health_check < self.health_period_s:
			return
		self._last_health_check = now
		battery = None
		try:
			battery = self.robot.get_battery()
		except Exception as exc:
			self._log("warn", f"battery telemetry unavailable: {exc}")

		platform = {}
		if self.telemetry is not None:
			try:
				platform = self.telemetry.read()
			except Exception as exc:
				self._log("warn", f"platform telemetry unavailable: {exc}")

		faults = self.health_monitor.evaluate(
			battery_fraction=battery,
			injected=self.fault_injector.active,
			**platform,
		)
		current_codes = {fault.code for fault in faults}
		self._handled_faults.intersection_update(current_codes)
		for fault in faults:
			if fault.code in self._handled_faults:
				continue
			self._handled_faults.add(fault.code)
			retry, verify = self._injected_recovery(fault)
			decision = self._handle_fault(fault, retry=retry, verify=verify)
			if decision in {RecoveryDecision.SAFE, RecoveryDecision.RETURN_HOME}:
				break

	def _injected_recovery(self, fault):
		if fault.code == FaultCode.CAMERA_FAILURE:
			self.fault_injector.clear(fault.code)
			recovered_frames = []

			def retry_camera():
				recovered_frames.append(self.robot.get_camera_frame())

			def verify_camera():
				return (bool(recovered_frames)
						and recovered_frames[-1] is not None
						and getattr(recovered_frames[-1], "image",
									recovered_frames[-1]) is not None)

			return retry_camera, verify_camera
		if fault.code == FaultCode.ULTRASONIC_FAILURE:
			sensor = getattr(self.navigator, "ultrasonic_sensor", None)
			if sensor is not None:
				self.fault_injector.clear(fault.code)
				recovered_distances = []

				def retry_ultrasonic():
					recovered_distances.append(sensor.read_distance_m())

				return retry_ultrasonic, lambda: (
					bool(recovered_distances) and recovered_distances[-1] > 0
				)
		return None, None

	def _navigation_step(self):
		now = self.clock()
		if self._last_nav_command is not None:
			previous, started = self._last_nav_command
			duration = max(0.0, now - started)
			if duration > 0 and (previous.v != 0.0 or previous.omega != 0.0):
				self._append_motion(previous.v, previous.omega, duration)
			self._last_nav_command = None

		try:
			result, command = self.navigator.step(self.robot)
		except (CameraError, UltrasonicError) as exc:
			code = (FaultCode.CAMERA_FAILURE if isinstance(exc, CameraError)
					else FaultCode.ULTRASONIC_FAILURE)
			self._handle_fault(Fault(code, Severity.RECOVERABLE, str(exc)))
			return
		except Exception as exc:
			self._handle_fault(Fault(FaultCode.NAVIGATION_FAILURE,
									 Severity.CRITICAL, str(exc)))
			return

		if command.behavior == "SAFE":
			self._enter_safe("navigator entered safe state")
			return
		if command.behavior == "SENSOR_STOP":
			self._handle_fault(Fault(FaultCode.ULTRASONIC_FAILURE,
									 Severity.RECOVERABLE,
									 "invalid front range data"))
			return
		if command.behavior == "TARGET_REACHED":
			if self.state != MissionState.APPROACH:
				self._transition(MissionState.APPROACH)
			self._transition(MissionState.MANIPULATE)
		elif result is not None and result.target.found:
			if self.state != MissionState.APPROACH:
				self._transition(MissionState.APPROACH)
		elif self.state != MissionState.SEARCH_TARGET:
			self._transition(MissionState.SEARCH_TARGET)

		if command.v != 0.0 or command.omega != 0.0:
			self._last_nav_command = (command, self.clock())

	def _manipulate(self):
		try:
			self.manipulator.perform_action()
			self._transition(MissionState.VERIFY_ACTION)
		except Exception as exc:
			self._handle_fault(Fault(FaultCode.MANIPULATION_FAILURE,
									 Severity.CRITICAL, str(exc)))

	def _verify_action(self):
		try:
			verified = self.manipulator.verify_action(self.robot)
		except Exception as exc:
			verified = False
			detail = str(exc)
		else:
			detail = "target remained visible after manipulation"
		if verified:
			self._transition(MissionState.RETURN_HOME)
		else:
			self._handle_fault(Fault(FaultCode.MANIPULATION_FAILURE,
									 Severity.CRITICAL, detail))

	def _return_step(self):
		now = self.clock()
		if self._return_active is not None:
			segment, deadline = self._return_active
			if now < deadline:
				return
			self.robot.stop()
			self._return_active = None

		if not self._return_queue:
			self.robot.stop()
			self._transition(MissionState.DONE)
			self.outcome = (MissionOutcome.ABORTED if self._return_as_abort
							else MissionOutcome.SUCCESS)
			self._log("info", f"mission result: {self.outcome.value}")
			return

		segment = self._return_queue.pop(0)
		self.robot.move(-segment.v, -segment.omega)
		self._return_active = (segment, now + segment.duration_s)

	def _handle_fault(self, fault, retry=None, verify=None):
		prior_state = self.state
		if self.state not in {MissionState.FAULT, MissionState.RECOVERY,
							  MissionState.SAFE_MODE, MissionState.DONE}:
			self._transition(MissionState.FAULT)
		if self.state == MissionState.FAULT:
			self._transition(MissionState.RECOVERY)

		if retry is None and verify is None:
			injected_retry, injected_verify = self._injected_recovery(fault)
			retry = injected_retry
			verify = injected_verify

		decision = self.fault_manager.handle(fault, self.robot, retry, verify)
		if decision == RecoveryDecision.RESUME:
			self._transition(prior_state)
		elif decision == RecoveryDecision.RETURN_HOME:
			self._return_as_abort = True
			self._begin_return()
		else:
			self._enter_safe(fault.detail or fault.code.value)
		return decision

	def _begin_return(self):
		if self.state != MissionState.RETURN_HOME:
			self._transition(MissionState.RETURN_HOME)
		self._finish_motion_segment()
		self._return_queue = list(reversed(self._motion_history))
		self._return_active = None
		self.robot.stop()

	def _finish_motion_segment(self):
		if self._last_nav_command is None:
			return
		command, started = self._last_nav_command
		duration = max(0.0, self.clock() - started)
		if duration > 0 and (command.v != 0.0 or command.omega != 0.0):
			self._append_motion(command.v, command.omega, duration)
		self._last_nav_command = None

	def _append_motion(self, v, omega, duration):
		if self._motion_history:
			last = self._motion_history[-1]
			if last.v == v and last.omega == omega:
				self._motion_history[-1] = MotionSegment(
					v, omega, last.duration_s + duration
				)
				return
		self._motion_history.append(MotionSegment(v, omega, duration))

	def _enter_safe(self, reason):
		self.robot.stop()
		self.manipulator.stop()
		if self.state not in {MissionState.SAFE_MODE, MissionState.DONE}:
			if self.state != MissionState.FAULT:
				self._transition(MissionState.FAULT)
			if self.state == MissionState.FAULT:
				self._transition(MissionState.RECOVERY)
			self._transition(MissionState.SAFE_MODE)
		self.outcome = MissionOutcome.SAFE
		self._log("error", f"SAFE MODE: {reason}")
		self._log("info", f"mission result: {self.outcome.value}")

	def _transition(self, destination):
		if not can_transition(self.state, destination):
			raise RuntimeError(f"invalid mission transition: {self.state.value} "
							   f"-> {destination.value}")
		previous = self.state
		self.state = destination
		self._log("state", f"{previous.value} -> {destination.value}")
		if destination == MissionState.RETURN_HOME:
			self._return_queue = list(reversed(self._motion_history))
			self._return_active = None

	def _log(self, method, event):
		if self.logger is not None:
			getattr(self.logger, method)(event)


def main():
	parser = argparse.ArgumentParser(description="Run the autonomous rover mission")
	parser.add_argument("--fault", choices=("camera", "motor", "battery",
											"communication"))
	args = parser.parse_args()

	from src.common.logger import EventLogger
	from src.fdir.health_monitor import FaultCode
	from src.hardware.adeept_telemetry import AdeeptTelemetry
	from src.hardware.real_robot import RealRobot
	from src.hardware.ultrasonic import UltrasonicSensor
	from src.manipulation.manipulator import AdeeptManipulator
	from src.navigation.navigator import Navigator

	logger = EventLogger("mission")
	robot = RealRobot()
	sensor = UltrasonicSensor()
	arm = AdeeptManipulator()
	fault_manager = FaultManager(logger=logger, manipulator=arm)
	injector = FaultInjector()
	if args.fault:
		fault_code = {
			"camera": FaultCode.CAMERA_FAILURE,
			"motor": FaultCode.MOTOR_FAILURE,
			"battery": FaultCode.BATTERY_CRITICAL,
			"communication": FaultCode.COMMUNICATION_LOSS,
		}[args.fault]
		injector.inject(fault_code)
	navigator = Navigator(ultrasonic_sensor=sensor,
						  fault_manager=fault_manager)
	manager = MissionManager(
		robot, navigator, arm, fault_manager=fault_manager,
		fault_injector=injector, telemetry=AdeeptTelemetry(), logger=logger,
	)
	try:
		print(manager.run().value)
	except KeyboardInterrupt:
		manager.emergency_stop()
	finally:
		robot.stop()
		arm.stop()
		sensor.cleanup()
		robot._camera.release()
		logger.close()


if __name__ == "__main__":
	main()
