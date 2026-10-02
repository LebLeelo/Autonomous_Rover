import unittest

from src.fdir.fault_manager import FaultManager, HealthState, RecoveryDecision
from src.fdir.health_monitor import FaultCode, FaultInjector, HealthMonitor, Severity
from src.hardware.adeept_telemetry import AdeeptTelemetry


class FakeRobot:
    def __init__(self):
        self.stops = 0

    def stop(self):
        self.stops += 1


class FakeLogger:
    def __init__(self):
        self.events = []

    def error(self, event): self.events.append(("error", event))
    def warn(self, event): self.events.append(("warn", event))
    def info(self, event): self.events.append(("info", event))


class FdirTests(unittest.TestCase):
    def test_battery_thresholds_classify_warning_and_critical(self):
        monitor = HealthMonitor()
        low = monitor.evaluate(battery_fraction=0.15)
        critical = monitor.evaluate(battery_fraction=0.09)
        self.assertEqual(low[0].code, FaultCode.BATTERY_LOW)
        self.assertEqual(critical[0].severity, Severity.CRITICAL)
        self.assertEqual(monitor.evaluate(battery_fraction=None), ())

    def test_platform_telemetry_triggers_critical_faults(self):
        class Info:
            @staticmethod
            def get_cpu_use(): return "95.0"
            @staticmethod
            def get_ram_info(): return "91.0"
            @staticmethod
            def get_cpu_tempfunc(): return "82.0"

        values = AdeeptTelemetry(Info()).read()
        faults = HealthMonitor().evaluate(**values)
        self.assertEqual({fault.code for fault in faults}, {
            FaultCode.CPU_OVERLOAD, FaultCode.MEMORY_HIGH,
            FaultCode.TEMPERATURE_CRITICAL,
        })

    def test_fault_injection_uses_normal_health_classification(self):
        injector = FaultInjector()
        injector.inject(FaultCode.CAMERA_FAILURE)
        faults = HealthMonitor().evaluate(injected=injector.active)
        self.assertEqual(faults[0].code, FaultCode.CAMERA_FAILURE)
        self.assertEqual(faults[0].severity, Severity.RECOVERABLE)
        injector.clear(FaultCode.CAMERA_FAILURE)
        self.assertFalse(injector.active)

    def test_recoverable_fault_resumes_only_after_verification(self):
        robot = FakeRobot()
        logger = FakeLogger()
        manager = FaultManager(logger=logger)
        fault = HealthMonitor().evaluate(camera_ok=False)[0]
        attempts = []
        decision = manager.handle(fault, robot, retry=lambda: attempts.append("retry"),
                                  verify=lambda: True)
        self.assertEqual(decision, RecoveryDecision.RESUME)
        self.assertEqual(manager.health, HealthState.NOMINAL)
        self.assertEqual(attempts, ["retry"])
        self.assertEqual([level for level, _ in logger.events],
                 ["error", "warn", "info"])

    def test_failed_recovery_latches_safe_state(self):
        robot = FakeRobot()
        manager = FaultManager()
        fault = HealthMonitor().evaluate(ultrasonic_ok=False)[0]
        decision = manager.handle(fault, robot, retry=lambda: None,
                                  verify=lambda: False)
        self.assertEqual(decision, RecoveryDecision.SAFE)
        self.assertEqual(manager.health, HealthState.SAFE)
        self.assertTrue(manager.safe_latched)
        self.assertGreaterEqual(robot.stops, 2)

    def test_critical_fault_stops_and_low_battery_requests_return(self):
        robot = FakeRobot()
        manager = FaultManager()
        critical = HealthMonitor().evaluate(motor_ok=False)[0]
        self.assertEqual(manager.handle(critical, robot), RecoveryDecision.SAFE)
        self.assertEqual(robot.stops, 1)

        manager = FaultManager()
        low_battery = HealthMonitor().evaluate(battery_fraction=0.15)[0]
        self.assertEqual(manager.handle(low_battery, robot), RecoveryDecision.RETURN_HOME)


if __name__ == "__main__":
    unittest.main()