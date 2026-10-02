# Verification Matrix

**SW PASS** means the cited software behavior passed with fakes or inspection. **PARTIAL** means only the software/interface portion is verified. **NOT RUN** means no applicable automated test was run. Physical verification is not represented as passing here.

| Requirement | Verification evidence | Software result | Hardware result / gap | Status |
|---|---|---|---|---|
| REQ-MIS-001 | `test_mission.MissionTests.test_complete_mission_manipulates_verifies_and_returns` | Scripted mission completes without operator input | No physical run | PARTIAL |
| REQ-MIS-002 | `test_mission.MissionTests.test_transient_camera_injection_recovers_without_skipping_self_test`; nominal mission | Camera, range, and tracked servo checks exercised with fakes | Servo state is not physical feedback | PARTIAL |
| REQ-MIS-003 | `src/mission/states.py`; mission/recovery tests | Explicit guarded states | Not applicable | SW PASS |
| REQ-MIS-004 | `test_mission.MissionTests.test_complete_mission_manipulates_verifies_and_returns` | `DONE`/`SUCCESS` outcome exercised | No physical result | PARTIAL |
| REQ-PER-001 | No image-based detector test currently exists | Not run | Camera, target, and color calibration untested | NOT RUN |
| REQ-PER-002 | `test_navigation.NavigationTests.test_obstacle_detector_classifies_front_range` | Front-range threshold and invalid reading logic pass | No physical range test | PARTIAL |
| REQ-PER-003 | `test_navigation.NavigationTests.test_camera_retry_is_verified_before_navigation_resumes` | Retry succeeds with fake camera | No physical test | PARTIAL |
| REQ-NAV-001 | `test_navigation.NavigationTests.test_target_bearing_maps_to_turn_direction`; scripted mission test | Decision and orchestration tested separately | Physical reachability untested; no localization | PARTIAL |
| REQ-NAV-002 | `test_navigation.NavigationTests.test_obstacle_turns_until_clear_distance` | Synthetic stop/turn/clear policy passes | Physical avoidance untested | PARTIAL |
| REQ-NAV-003 | `test_navigation.NavigationTests.test_invalid_obstacle_reading_stops`; critical-fault mission tests | Software stop path passes | Stop time and physical actuator response untested | PARTIAL |
| REQ-MAN-001 | Nominal mission flow; target-reached branch | Manipulation follows target-reached result | Physical alignment/standoff untested | PARTIAL |
| REQ-MAN-002 | `test_manipulator.ManipulatorTests.test_grasp_sequence_uses_arm_and_gripper_channels` | Servo command sequence passes | Physical arm actuation untested | PARTIAL |
| REQ-MAN-003 | `test_mission.MissionTests.test_failed_action_verification_enters_safe_mode`; `test_manipulator.ManipulatorTests.test_action_verification_requires_target_to_disappear` | Visibility gates continuation | Does not prove grasp or movement | PARTIAL |
| REQ-FDIR-001 | `test_fdir.FdirTests.test_platform_telemetry_triggers_critical_faults`; periodic polling inspection | Telemetry classification passes | No Pi telemetry run; battery optional | PARTIAL |
| REQ-FDIR-002 | Camera, motor, and communication injection tests | Supported paths classified/handled | Motor/communication are injected, not hardware-detected | PARTIAL |
| REQ-FDIR-003 | `test_fdir.FdirTests.test_battery_thresholds_classify_warning_and_critical`; critical fault test | Recoverable/critical classification passes | Physical sources untested | SW PASS |
| REQ-FDIR-004 | `test_navigation.NavigationTests.test_camera_retry_is_verified_before_navigation_resumes`; `test_fdir.FdirTests.test_recoverable_fault_resumes_only_after_verification` | Retry/recovery passes | Physical recovery untested | SW PASS |
| REQ-FDIR-005 | `test_fdir.FdirTests.test_recoverable_fault_resumes_only_after_verification`; `test_fdir.FdirTests.test_failed_recovery_latches_safe_state` | Resume depends on verification | Physical health restoration untested | SW PASS |
| REQ-FDIR-006 | `test_mission.MissionTests.test_injected_motor_fault_enters_safe_before_mission`; failed recovery test | Stop calls and safe latch pass | Physical stop untested | PARTIAL |
| REQ-SAF-001 | `test_mission.MissionTests.test_emergency_stop_enters_safe_and_stops_actuators` | Software emergency-stop API passes with fakes | No physical switch/response-time test | PARTIAL |
| REQ-SAF-002 | Motor/communication injection and latched-safe navigation tests | Mission is interrupted before manipulation | Hardware interlock untested | PARTIAL |
| REQ-OBS-001 | `test_observability.ObservabilityTests.test_event_logger_persists_timestamped_state_fault_and_result`; mission transition test | Timestamped logs and transition calls verified | Rover log collection untested | SW PASS |
| REQ-OBS-002 | FDIR recovery logging assertion; observability persistence test | Fault/recovery logging verified in software | Rover log collection untested | SW PASS |
| REQ-OBS-003 | Nominal mission outcome and observability persistence tests | Mission outcome logging verified in software | Physical result unavailable | SW PASS |

## Naming Crosswalk

Requirement vocabulary maps to implementation as follows: `INIT` to `BOOT`/`SELF_TEST`; `NAVIGATION` to `NAVIGATE`/`SEARCH_TARGET`/`APPROACH`; `MANIPULATION` to `MANIPULATE`/`VERIFY_ACTION`; `SAFE` to `SAFE_MODE`; `COMPLETE` to `DONE` with a `SUCCESS` outcome. See [requirements.md](requirements.md) for scope-compatible wording.