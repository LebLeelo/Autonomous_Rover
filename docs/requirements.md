# System Requirements Specification

## Autonomous Rover

## 1. Purpose

This document defines the system requirements for the Autonomous Rover project.

The objective is to demonstrate autonomous operation, perception, navigation, manipulation, fault detection and recovery on a small robotic platform.

The requirements describe **what the system shall do**. Implementation choices are defined separately in the system architecture and design documentation.

---

## 2. Scope

The system consists of a Raspberry Pi-based mobile rover equipped with:

* A camera
* Motorized wheels
* A robotic arm
* On-board computing
* Sensors required for navigation and health monitoring

The rover shall perform a predefined autonomous mission, detect a target, approach and manipulate it, and handle selected injected faults.

---

## 3. System Requirements

### 3.1 Mission

| ID | Name | Requirement | Rationale | Verification Method | Verification Criteria |
|---|---|---|---|---|---|
| **REQ-MIS-001** | Autonomous Mission | The system shall execute a predefined mission without continuous operator intervention | Demonstrate autonomous system operation | Test | A complete mission shall be executed without manual control |
| **REQ-MIS-002** | System Initialization | The system shall perform an initialization and self-test sequence before starting the mission | Ensure that required system components are operational before mission execution | Test | The rover shall check required components and report the result before entering the mission state |
| **REQ-MIS-003** | Mission State Management | The system shall explicitly represent its operational state | Provide deterministic mission management and support fault handling | Inspection / Test | The software shall implement explicit states including at least `INIT`, `NAVIGATION`, `MANIPULATION`, `RECOVERY`, `SAFE` and `COMPLETE`|
| **REQ-MIS-004** | Mission Completion | The system shall detect and record successful mission completion | Provide an unambiguous mission outcome | Test | The system shall enter the `COMPLETE` state after all mission objectives have been fulfilled |


### 3.2 Perception

| ID | Name | Requirement | Rationale | Verification Method | Verification Criteria |
|---|---|---|---|---|---|
| **REQ-PER-001** | Target Detection | The system shall detect the mission target using the onboard camera | Enable autonomous target acquisition | Test | The target shall be detected in representative test conditions |
| **REQ-PER-002** | Obstacle Detection | The system shall detect obstacles within the relevant operating area | Prevent collisions during autonomous navigation | Test | The system shall detect representative obstacles placed in the rover's path |
| **REQ-PER-003** | Invalid Perception Handling | The system shall detect invalid or unavailable perception data and transition to a safe behavior | Prevent unsafe decisions based on unreliable sensor information | Fault injection / Test | Disabling or invalidating the camera input shall trigger the defined fault-handling behavior |

### 3.3 Navigation

| ID | Name | Requirement | Rationale | Verification Method | Verification Criteria |
|---|---|---|---|---|---|
| **REQ-NAV-001** | Autonomous Navigation | The system shall autonomously navigate toward the mission target | Demonstrate autonomous mobility | Test | The rover shall reach the target area without manual driving |
| **REQ-NAV-002** | Obstacle Avoidance | The system shall modify its trajectory when an obstacle blocks the planned path | Reduce collision risk during autonomous navigation | Test | The rover shall stop, avoid or re-plan around a representative obstacle |
| **REQ-NAV-003** | Safe Stop | The system shall stop its motion when continued navigation is unsafe | Provide a deterministic safe behavior | Test | The rover shall stop its motors following a defined critical navigation fault |

### 3.4 Manipulation

| ID | Name | Requirement | Rationale | Verification Method | Verification Criteria |
|---|---|---|---|---|---|
| **REQ-MAN-001** | Target Approach | The system shall position the rover within the defined manipulation area before activating the robotic arm | Ensure that manipulation is attempted only from a suitable position | Test | The rover shall reach the predefined manipulation position before arm activation |
| **REQ-MAN-002** | Object Manipulation | The system shall execute a predefined manipulation sequence using the robotic arm | Demonstrate autonomous interaction with the physical environment | Test | The arm shall execute the complete predefined sequence without manual intervention |
| **REQ-MAN-003** | Manipulation Verification | The system shall determine whether the manipulation operation was successful | Prevent the mission from continuing based on an assumed successful action | Test | The system shall report either `SUCCESS` or `FAILURE` after the manipulation sequence |

### 3.5 Fault Detection, Isolation and Recovery

| ID | Name | Requirement | Rationale | Verification Method | Verification Criteria |
|---|---|---|---|---|---|
| **REQ-FDIR-001** | Health Monitoring | The system shall monitor the health status of critical software and hardware components | Enable detection of abnormal system behavior | Test | The health monitor shall periodically evaluate the status of defined critical components |
| **REQ-FDIR-002** | Fault Detection | The system shall detect selected failures affecting mission execution | Enable autonomous fault management | Fault injection / Test | At least camera, actuator and communication faults shall be detectable |
| **REQ-FDIR-003** | Fault Classification | The system shall classify detected faults according to their severity | Enable appropriate recovery decisions | Inspection / Test | Faults shall be classified into at least recoverable and critical categories |
| **REQ-FDIR-004** | Fault Recovery | The system shall attempt an appropriate recovery action for recoverable faults | Maintain mission execution when possible | Fault injection / Test | At least one representative recoverable fault shall trigger an automatic recovery action |
| **REQ-FDIR-005** | Recovery Verification | The system shall verify that the recovery action restored the affected function before resuming the mission | Prevent continuation after an unsuccessful recovery | Test | The system shall perform a health check after recovery and either resume the mission or enter a safe state |
| **REQ-FDIR-006** | Safe State | The system shall enter a safe state when a critical fault cannot be recovered | Limit the consequences of critical failures | Fault injection / Test | The rover shall stop its actuators and remain in the `SAFE` state after a critical unrecoverable fault |

### 3.6 Safety

| ID | Name | Requirement | Rationale | Verification Method | Verification Criteria |
|---|---|---|---|---|---|
| **REQ-SAF-001** | Emergency Stop | The system shall provide a mechanism to immediately stop rover motion | Provide a manual safety mechanism during testing | Test | Activation of the emergency stop shall stop the rover's motors |
| **REQ-SAF-002** | Safety Priority | Safety-related actions shall take priority over mission execution | Prevent mission logic from overriding safety behavior | Inspection / Test | A safety-triggered stop shall interrupt an active mission state |

### 3.7 Observability

| ID | Name | Requirement | Rationale | Verification Method | Verification Criteria |
|---|---|---|---|---|---|
| **REQ-OBS-001** | State Logging | The system shall log mission state transitions | Support debugging and post-mission analysis | Inspection / Test | Each state transition shall generate a timestamped log entry |
| **REQ-OBS-002** | Fault Logging | The system shall log detected faults and associated recovery actions | Provide traceability of system failures and responses | Test | Injected faults shall appear in the system logs together with their response |
| **REQ-OBS-003** | Mission Result | The system shall record the final mission outcome | Enable objective evaluation of mission execution | Test | The final log shall indicate at least `SUCCESS`, `ABORTED` or `SAFE` |

---

## 4. Requirement Traceability

Each requirement shall be traceable to its implementation and verification test.

| Requirement  | Implementation      | Verification  |
| ------------ | ------------------- | ------------- |
| REQ-MIS-001  | Mission Manager     | TEST-MIS-001  |
| REQ-PER-001  | Perception Module   | TEST-PER-001  |
| REQ-NAV-001  | Navigation Module   | TEST-NAV-001  |
| REQ-MAN-002  | Manipulation Module | TEST-MAN-001  |
| REQ-FDIR-002 | Health Monitor      | TEST-FDIR-001 |
| REQ-FDIR-006 | Safety Manager      | TEST-SAF-001  |
| REQ-OBS-001  | Logger              | TEST-OBS-001  |

The complete traceability matrix shall be maintained as implementation progresses.

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
