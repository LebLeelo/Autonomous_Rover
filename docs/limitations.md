# Limitations

- **Return:** recorded commands are replayed in reverse using elapsed time. There is no wheel odometry, map, or absolute localization; wheel slip or a changed course invalidates the estimate.
- **Navigation:** the policy uses target bearing/range and one forward-facing ultrasonic sensor. It turns in a fixed direction around a close obstacle and does not globally plan or guarantee clearance on all sides.
- **Perception:** target detection uses configured color thresholds and apparent size. Lighting, calibration, occlusion, and background colors affect detection. The physical camera has not been validated in this report.
- **Manipulation:** the open/lower/grip/lift action is timed and assumes Adeept servo channels 2 and 4 with stock direction settings. Verify channels, directions, pulse duration, and mechanical clearance before use.
- **Manipulation verification:** success currently means the configured target detector no longer sees the target in verification frames. This does not prove that the object was grasped or moved.
- **Actuators:** there is no encoder, motor-current sensor, or physical servo feedback. `returnServoAngle()` reports the servo driver's tracked command state.
- **Fault monitoring:** battery monitoring requires an injected reader. Motor and communication faults are injected scenarios, not detected from hardware signals.
- **Safety:** `emergency_stop()` is a software API; there is no physical emergency-stop switch or independent safety controller.
- **Validation:** unit tests use fake devices on a development machine. They do not establish physical mission success, collision rate, repeatability, timing guarantees, or safe operation.
- **Standards:** this project is not ECSS-compliant or safety-certified software.