from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional


class FaultCode(str, Enum):
    CAMERA_FAILURE = "CAMERA_FAILURE"
    ULTRASONIC_FAILURE = "ULTRASONIC_FAILURE"
    MOTOR_FAILURE = "MOTOR_FAILURE"
    BATTERY_LOW = "BATTERY_LOW"
    BATTERY_CRITICAL = "BATTERY_CRITICAL"
    COMMUNICATION_LOSS = "COMMUNICATION_LOSS"
    INVALID_SENSOR_DATA = "INVALID_SENSOR_DATA"
    CPU_OVERLOAD = "CPU_OVERLOAD"
    MEMORY_HIGH = "MEMORY_HIGH"
    TEMPERATURE_CRITICAL = "TEMPERATURE_CRITICAL"
    MANIPULATION_FAILURE = "MANIPULATION_FAILURE"
    MISSION_TIMEOUT = "MISSION_TIMEOUT"
    NAVIGATION_FAILURE = "NAVIGATION_FAILURE"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class Severity(str, Enum):
    RECOVERABLE = "RECOVERABLE"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class Fault:
    code: FaultCode
    severity: Severity
    detail: str = ""


class HealthMonitor:
    def __init__(self, warning_battery=0.20, critical_battery=0.10,
                 max_cpu_percent=90.0, max_memory_percent=90.0,
                 max_temperature_c=80.0):
        if not 0.0 <= critical_battery < warning_battery <= 1.0:
            raise ValueError("battery thresholds must satisfy 0 <= critical < warning <= 1")
        self.warning_battery = warning_battery
        self.critical_battery = critical_battery
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_percent = max_memory_percent
        self.max_temperature_c = max_temperature_c

    def evaluate(self, *, camera_ok: Optional[bool] = None,
                 ultrasonic_ok: Optional[bool] = None,
                 motor_ok: Optional[bool] = None,
                 communication_ok: Optional[bool] = None,
                 battery_fraction: Optional[float] = None,
                 cpu_percent: Optional[float] = None,
                 memory_percent: Optional[float] = None,
                 temperature_c: Optional[float] = None,
                 injected: Iterable[FaultCode] = ()) -> tuple[Fault, ...]:
        faults = []
        if camera_ok is False:
            faults.append(Fault(FaultCode.CAMERA_FAILURE, Severity.RECOVERABLE,
                                "camera unavailable"))
        if ultrasonic_ok is False:
            faults.append(Fault(FaultCode.ULTRASONIC_FAILURE, Severity.RECOVERABLE,
                                "ultrasonic sensor unavailable"))
        if motor_ok is False:
            faults.append(Fault(FaultCode.MOTOR_FAILURE, Severity.CRITICAL,
                                "motor response unavailable"))
        if communication_ok is False:
            faults.append(Fault(FaultCode.COMMUNICATION_LOSS, Severity.CRITICAL,
                                "communication unavailable"))
        if battery_fraction is not None:
            if not 0.0 <= battery_fraction <= 1.0:
                faults.append(Fault(FaultCode.INVALID_SENSOR_DATA,
                                    Severity.RECOVERABLE, "battery outside 0..1"))
            elif battery_fraction < self.critical_battery:
                faults.append(Fault(FaultCode.BATTERY_CRITICAL, Severity.CRITICAL,
                                    f"battery={battery_fraction:.2f}"))
            elif battery_fraction < self.warning_battery:
                faults.append(Fault(FaultCode.BATTERY_LOW, Severity.RECOVERABLE,
                                    f"battery={battery_fraction:.2f}"))
        if cpu_percent is not None and cpu_percent >= self.max_cpu_percent:
            faults.append(Fault(FaultCode.CPU_OVERLOAD, Severity.CRITICAL,
                                f"cpu={cpu_percent:.1f}%"))
        if memory_percent is not None and memory_percent >= self.max_memory_percent:
            faults.append(Fault(FaultCode.MEMORY_HIGH, Severity.CRITICAL,
                                f"memory={memory_percent:.1f}%"))
        if temperature_c is not None and temperature_c >= self.max_temperature_c:
            faults.append(Fault(FaultCode.TEMPERATURE_CRITICAL, Severity.CRITICAL,
                                f"temperature={temperature_c:.1f} C"))

        for code in injected:
            if code not in {fault.code for fault in faults}:
                faults.append(Fault(code, _severity_for(code), "fault injected"))
        return tuple(faults)


class FaultInjector:
    """Explicit test/demo fault switches; injected faults use normal FDIR paths."""

    def __init__(self):
        self._active = set()

    def inject(self, code: FaultCode):
        self._active.add(FaultCode(code))

    def clear(self, code: FaultCode):
        self._active.discard(FaultCode(code))

    @property
    def active(self) -> frozenset[FaultCode]:
        return frozenset(self._active)


def _severity_for(code: FaultCode) -> Severity:
    if code in {FaultCode.MOTOR_FAILURE, FaultCode.BATTERY_CRITICAL,
                FaultCode.COMMUNICATION_LOSS, FaultCode.CPU_OVERLOAD,
                FaultCode.MEMORY_HIGH, FaultCode.TEMPERATURE_CRITICAL,
                FaultCode.MANIPULATION_FAILURE, FaultCode.MISSION_TIMEOUT,
                FaultCode.NAVIGATION_FAILURE, FaultCode.EMERGENCY_STOP}:
        return Severity.CRITICAL
    return Severity.RECOVERABLE