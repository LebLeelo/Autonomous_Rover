from enum import Enum
from typing import Callable, Optional

from src.fdir.health_monitor import Fault, FaultCode, Severity


class HealthState(str, Enum):
    NOMINAL = "NOMINAL"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    SAFE = "SAFE"


class RecoveryDecision(str, Enum):
    RESUME = "RESUME"
    RETURN_HOME = "RETURN_HOME"
    SAFE = "SAFE"


class FaultManager:
    def __init__(self, logger=None, max_attempts=1, manipulator=None):
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.logger = logger
        self.max_attempts = max_attempts
        self.manipulator = manipulator
        self.health = HealthState.NOMINAL
        self.safe_latched = False

    def handle(self, fault: Fault, robot,
               retry: Optional[Callable[[], None]] = None,
               verify: Optional[Callable[[], bool]] = None) -> RecoveryDecision:
        self._log("error", f"fault detected: {fault.code.value} ({fault.severity.value})")
        if self.safe_latched:
            return RecoveryDecision.SAFE

        if fault.code == FaultCode.BATTERY_LOW:
            self.health = HealthState.DEGRADED
            self._log("warn", "low battery: request return home")
            return RecoveryDecision.RETURN_HOME

        if fault.severity == Severity.CRITICAL:
            return self._enter_safe(robot, fault.code.value)

        self.health = HealthState.DEGRADED
        robot.stop()
        if retry is not None and verify is not None:
            for attempt in range(1, self.max_attempts + 1):
                self._log("warn", f"recovery attempt {attempt}: {fault.code.value}")
                try:
                    retry()
                    if verify():
                        self.health = HealthState.NOMINAL
                        self._log("info", f"recovery verified: {fault.code.value}")
                        return RecoveryDecision.RESUME
                except Exception as exc:
                    self._log("error", f"recovery failed: {exc}")
        return self._enter_safe(robot, f"recovery failed: {fault.code.value}")

    def _enter_safe(self, robot, reason):
        robot.stop()
        if self.manipulator is not None:
            self.manipulator.stop()
        self.health = HealthState.SAFE
        self.safe_latched = True
        self._log("error", f"SAFE state: {reason}")
        return RecoveryDecision.SAFE

    def _log(self, method, event):
        if self.logger is not None:
            getattr(self.logger, method)(event)