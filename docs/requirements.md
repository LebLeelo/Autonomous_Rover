# System Requirements Specification

## Autonomous Rover

## 1. Purpose

This document defines the system requirements for the Autonomous Rover project.

The objective is to demonstrate autonomous operation, perception, navigation, manipulation, fault detection and recovery on a small robotic platform.

The requirements describe **what the system shall do**. Implementation choices are defined separately in the system architecture and design documentation.

---

## 2. Scope

The system consists of a Raspberry Pi-based Adeept PiCar Pro equipped with:

* A camera
* Motorized wheels
* A robotic arm
* On-board computing
* An onboard camera
* A forward-facing ultrasonic range sensor
* Servo-driven arm/gripper controlled by the Adeept servo board

The rover shall perform a predefined autonomous mission, detect a target, approach and manipulate it, and handle selected injected faults.

---

## 3. System Requirements

### 3.1 Mission

| ID | Name | Requirement | Rationale | Verification Method | Verification Criteria |
|---|---|---|---|---|---|
| **REQ-MIS-001** | Autonomous Mission | The system shall execute the configured search, approach, manipulation, verification, and return sequence without continuous operator commands | Demonstrate autonomous mission orchestration within the supported course | Test | The software mission reaches a terminal outcome using the defined component interfaces; physical course performance is separately verified |
| **REQ-MIS-002** | System Initialization | The system shall check camera capture, ultrasonic range availability, and configured servo-driver state before mission execution | Detect unavailable components before issuing mission commands | Test | A valid frame, in-range front distance, and readable tracked arm/gripper servo states are required to enter `IDLE`; tracked servo values are not physical feedback |
| **REQ-MIS-003** | Mission State Management | The system shall explicitly represent mission and fault-handling states | Provide deterministic mission management and support fault handling | Inspection / Test | The software implements `BOOT`, `SELF_TEST`, `IDLE`, navigation/search/approach, manipulation/verification, return, `RECOVERY`, `SAFE_MODE`, and `DONE` |
| **REQ-MIS-004** | Mission Completion | The system shall record a terminal mission outcome | Provide an unambiguous mission result | Test | Nominal return logs `SUCCESS`; low-battery return logs `ABORTED`; unrecoverable critical fault logs `SAFE` |


### 3.2 Perception

| ID | Name | Requirement | Rationale | Verification Method | Verification Criteria |
|---|---|---|---|---|---|
| **REQ-PER-001** | Target Detection | The system shall detect a target matching the configured color profile in camera frames | Enable target acquisition without requiring a trained model | Test | Detector returns target presence, normalized horizontal bearing, and calibrated apparent-size range for a labeled test set |
| **REQ-PER-002** | Front Obstacle Detection | The system shall classify valid readings from the single forward-facing ultrasonic sensor | Reduce risk of driving into a close frontal obstacle | Test | A valid reading at or below 0.60 m is classified as detected; invalid readings are rejected; sensor range is limited to the Adeept driver's 2 m maximum |
| **REQ-PER-003** | Invalid Camera Handling | The system shall retry a failed camera capture once and avoid navigation on an unavailable frame | Prevent decisions based on absent camera data | Fault injection / Test | A valid retry resumes processing; an unsuccessful retry enters the safe behavior |

### 3.3 Navigation

| ID | Name | Requirement | Rationale | Verification Method | Verification Criteria |
|---|---|---|---|---|---|
| **REQ-NAV-001** | Local Target Approach | The system shall steer toward a detected target using image bearing and calibrated apparent-size range | Support local approach without claiming localization | Test | Off-center detections produce a turn toward target; centered detections outside 0.45 m produce forward motion; a centered detection inside 0.45 m reports target reached |
| **REQ-NAV-002** | Front Obstacle Response | The system shall stop and turn when valid front range is at or below 0.30 m | Reduce immediate frontal collision risk | Test | Controller commands a turn and holds avoidance until front range exceeds 0.60 m; this does not guarantee route clearance |
| **REQ-NAV-003** | Safe Stop | The system shall stop the drive when range is invalid or a critical fault is active | Provide deterministic behavior when motion is unsafe | Test | Invalid range and latched critical faults issue `stop()` and no forward command |

### 3.4 Manipulation

| ID | Name | Requirement | Rationale | Verification Method | Verification Criteria |
|---|---|---|---|---|---|
| **REQ-MAN-001** | Manipulation Standoff | The system shall command manipulation only after the target is centered and its estimated range is at or below 0.45 m | Avoid arm activation before configured standoff estimate | Test | `TARGET_REACHED` is reported only for a centered detection inside the configured range threshold |
| **REQ-MAN-002** | Arm/Gripper Command Sequence | The system shall issue the configured open, lower, grip, and lift servo commands | Demonstrate mission integration with the Adeept arm/gripper interface | Test | Expected commands are sent to configured channels 4 and 2 in sequence; physical motion requires hardware verification |
| **REQ-MAN-003** | Visual Action Check | The system shall report the post-action visibility result for the configured target | Avoid assuming a sent servo command changed the camera scene | Test | Target absent in verification frames is reported as action success; target remaining visible is a failure. This does not prove grasp or displacement |

### 3.5 Fault Detection, Isolation and Recovery

| ID | Name | Requirement | Rationale | Verification Method | Verification Criteria |
|---|---|---|---|---|---|
| **REQ-FDIR-001** | Available Health Monitoring | The system shall periodically evaluate available CPU, RAM, temperature, and optional battery telemetry, and check camera/range inputs when used | Monitor only signals exposed by rover APIs | Test | Configured thresholds produce faults; unavailable optional telemetry remains unknown rather than fabricated |
| **REQ-FDIR-002** | Fault Detection and Injection | The system shall detect camera/range errors and accept injected motor, communication, and battery fault scenarios | Exercise response paths without claiming absent hardware feedback | Fault injection / Test | Camera/range errors are detected at their adapters; injected critical flags are classified and handled by FDIR |
| **REQ-FDIR-003** | Fault Classification | The system shall classify detected faults according to their severity | Enable appropriate recovery decisions | Inspection / Test | Faults shall be classified into at least recoverable and critical categories |
| **REQ-FDIR-004** | Fault Recovery | The system shall attempt an appropriate recovery action for recoverable faults | Maintain mission execution when possible | Fault injection / Test | At least one representative recoverable fault shall trigger an automatic recovery action |
| **REQ-FDIR-005** | Recovery Verification | The system shall verify that the recovery action restored the affected function before resuming the mission | Prevent continuation after an unsuccessful recovery | Test | The system shall perform a health check after recovery and either resume the mission or enter a safe state |
| **REQ-FDIR-006** | Safe State | The system shall enter a safe state on an unrecoverable or critical fault | Limit consequences using available actuator commands | Fault injection / Test | Drive stop and Adeept servo `stopWiggle()` are called, and mission state remains `SAFE_MODE`; physical stopping requires rover test |

### 3.6 Safety

| ID | Name | Requirement | Rationale | Verification Method | Verification Criteria |
|---|---|---|---|---|---|
| **REQ-SAF-001** | Software Emergency Stop | The mission manager shall expose an emergency-stop API | Allow an operator/controller to interrupt mission execution | Test | Calling `emergency_stop()` stops drive and servo commands and enters `SAFE_MODE`; there is no physical switch in this scope |
| **REQ-SAF-002** | Safety Priority | Safety-related actions shall take priority over mission execution | Prevent mission logic from overriding safety behavior | Inspection / Test | A safety-triggered stop shall interrupt an active mission state |

### 3.7 Observability

| ID | Name | Requirement | Rationale | Verification Method | Verification Criteria |
|---|---|---|---|---|---|
| **REQ-OBS-001** | State Logging | The system shall log mission state transitions | Support debugging and post-mission analysis | Inspection / Test | Each state transition shall generate a timestamped log entry |
| **REQ-OBS-002** | Fault Logging | The system shall log detected faults and associated recovery actions | Provide traceability of system failures and responses | Test | Injected faults shall appear in the system logs together with their response |
| **REQ-OBS-003** | Mission Result | The system shall record the final mission outcome | Enable objective evaluation of mission execution | Test | The final log shall indicate at least `SUCCESS`, `ABORTED` or `SAFE` |

---

## 4. Requirement Traceability

The complete requirement-to-test mapping and current verification status are maintained in [verification_matrix.md](verification_matrix.md). Requirement state names are cross-referenced there to the implementation state names.

---

## 5. Verification Methods

The following verification methods are used:

* **Inspection** — verification through examination of the software architecture or implementation.
* **Test** — verification through execution on the rover.
* **Fault Injection** — deliberate introduction of a fault to verify detection and recovery behavior.

Each implemented requirement shall have at least one corresponding verification activity.

---

## 6. Project Boundaries

The following are outside the scope of this project:

* Full SLAM and global mapping
* Formal real-time guarantees
* Redundant hardware
* Formal safety certification
* Space-qualified hardware
* ECSS compliance certification
* Machine-learning-based global path planning
* Operation in arbitrary unstructured environments

The project demonstrates selected **systems engineering, software engineering, verification and fault-management practices** on a small robotic platform.
