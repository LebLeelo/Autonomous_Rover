"""Adapter the Adeept ultrasonic driver to the project's meter-based API."""

from src.common import config
from src.common.errors import UltrasonicError


class UltrasonicSensor:
    def __init__(self, driver=None):
        if driver is None:
            import Ultra as driver
        self._driver = driver

    def read_distance_m(self) -> float:
        try:
            distance_m = float(self._driver.checkdist()) / 100.0
        except Exception as exc:
            raise UltrasonicError(f"ultrasonic read failed: {exc}") from exc
        if not (config.ULTRASONIC_MIN_VALID_M <= distance_m
                <= min(config.ULTRASONIC_MAX_VALID_M, 2.0)):
            raise UltrasonicError(f"implausible reading: {distance_m:.2f} m")
        return distance_m

    def cleanup(self):
        sensor = getattr(self._driver, "sensor", None)
        if sensor is not None:
            sensor.close()