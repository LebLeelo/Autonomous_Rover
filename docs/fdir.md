# Fault Detection, Isolation and Recovery

## Detection Inputs

The monitor evaluates CPU, RAM, and temperature when the Adeept `Info` adapter is available, and battery fraction only when a battery reader is configured. Camera and ultrasonic failures are observed at startup or when those devices are used. Motor and communication failures have no physical feedback source in this integration; they are explicit injected scenarios.

## Classification and Response

| Fault | Classification | Response |
|---|---|---|
| Camera capture unavailable | Recoverable | Stop, retry once, verify a usable frame; otherwise `SAFE_MODE` |
| Ultrasonic read unavailable/invalid | Recoverable | Stop, retry once, verify positive in-range reading; otherwise `SAFE_MODE` |
| Battery below 20% | Recoverable/degraded | Request best-effort return |
| Battery below 10% | Critical | Stop drive and servo motion; latch `SAFE_MODE` |
| Motor failure injection | Critical | Stop drive and servo motion; latch `SAFE_MODE` |
| Communication loss injection | Critical | Stop drive and servo motion; latch `SAFE_MODE` |
| CPU >= 90%, RAM >= 90%, or CPU temperature >= 80 C | Critical | Stop drive and servo motion; latch `SAFE_MODE` |
| Manipulation verification failure | Critical | Stop drive and servo motion; latch `SAFE_MODE` |

These thresholds are implementation defaults, not validated safety limits. Battery is unknown unless a reader is configured. Motor and communication injection validates software response, not physical fault detection.

## Recovery Verification

`FaultManager` resumes only when a retry callback and successful verification callback are provided. Camera verification checks that a frame exists; range verification checks for a positive reading. These checks establish availability, not measurement accuracy. A persistent or critical fault stops the robot and manipulator and latches health at `SAFE`.

## Injection

From the repository root, `python -m src.mission.mission_manager --fault camera|motor|battery|communication` activates a software fault input before mission execution. Camera injection exercises recovery; motor, critical battery, and communication injection exercise the safe-state path. Low-battery return is also covered by unit tests.