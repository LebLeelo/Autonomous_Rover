"""Hiérarchie de fautes."""

class RobotError(Exception):
    """Base de toutes les fautes détectables par le HealthMonitor."""
    severity = "RECOVERABLE"      # classification par défaut


class CameraError(RobotError):
    severity = "CRITICAL"          # cf. docs/fdir.md — à ajuster selon ta classification


class UltrasonicError(RobotError):
    severity = "RECOVERABLE"       # perte temporaire → navigation dégradée possible


class MotorError(RobotError):
    severity = "CRITICAL"


class BatteryError(RobotError):
    severity = "CRITICAL"