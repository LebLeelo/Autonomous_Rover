"""Le seul module qui parle à l'ultrason (HC-SR04 via RPi.GPIO).

⚠️ ADAPTE TRIG_PIN / ECHO_PIN à ton câblage réel.
Évite les broches des moteurs : 4, 17, 26, 21, 27, 18.
"""
import time

import RPi.GPIO as GPIO

from src.common import config
from src.common.errors import UltrasonicError

TRIG_PIN = 23
ECHO_PIN = 24


class UltrasonicSensor:
    def __init__(self, trig=TRIG_PIN, echo=ECHO_PIN, timeout_s=0.03):
        self.trig = trig
        self.echo = echo
        self.timeout_s = timeout_s
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trig, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.echo, GPIO.IN)

    def read_distance_m(self) -> float:
        # impulsion de déclenchement (10 µs)
        GPIO.output(self.trig, True)
        time.sleep(0.00001)
        GPIO.output(self.trig, False)

        t0 = time.time()
        while GPIO.input(self.echo) == 0:          # attente du front montant
            if time.time() - t0 > self.timeout_s:
                raise UltrasonicError("no echo pulse (sensor not responding)")
        pulse_start = time.time()

        while GPIO.input(self.echo) == 1:          # attente du front descendant
            if time.time() - pulse_start > self.timeout_s:
                raise UltrasonicError("echo pulse too long")
        pulse_end = time.time()

        distance = (pulse_end - pulse_start) * 343.0 / 2.0
        if not (config.ULTRASONIC_MIN_VALID_M <= distance
                <= config.ULTRASONIC_MAX_VALID_M):
            raise UltrasonicError(f"implausible reading: {distance:.2f} m")
        return distance

    def cleanup(self):
        GPIO.cleanup((self.trig, self.echo))