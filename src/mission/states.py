from enum import Enum


class MissionState(str, Enum):
	BOOT = "BOOT"
	SELF_TEST = "SELF_TEST"
	IDLE = "IDLE"
	MISSION = "MISSION"
	NAVIGATE = "NAVIGATE"
	SEARCH_TARGET = "SEARCH_TARGET"
	APPROACH = "APPROACH"
	MANIPULATE = "MANIPULATE"
	VERIFY_ACTION = "VERIFY_ACTION"
	RETURN_HOME = "RETURN_HOME"
	FAULT = "FAULT"
	RECOVERY = "RECOVERY"
	SAFE_MODE = "SAFE_MODE"
	DONE = "DONE"


class MissionOutcome(str, Enum):
	SUCCESS = "SUCCESS"
	ABORTED = "ABORTED"
	SAFE = "SAFE"


TRANSITIONS = {
	MissionState.BOOT: {MissionState.SELF_TEST},
	MissionState.SELF_TEST: {MissionState.IDLE, MissionState.FAULT},
	MissionState.IDLE: {MissionState.MISSION, MissionState.FAULT},
	MissionState.MISSION: {MissionState.NAVIGATE, MissionState.FAULT,
						   MissionState.RETURN_HOME},
	MissionState.NAVIGATE: {MissionState.SEARCH_TARGET, MissionState.APPROACH,
							MissionState.FAULT, MissionState.RETURN_HOME},
	MissionState.SEARCH_TARGET: {MissionState.APPROACH, MissionState.FAULT,
								 MissionState.RETURN_HOME},
	MissionState.APPROACH: {MissionState.SEARCH_TARGET, MissionState.MANIPULATE,
							MissionState.FAULT, MissionState.RETURN_HOME},
	MissionState.MANIPULATE: {MissionState.VERIFY_ACTION, MissionState.FAULT,
							  MissionState.RETURN_HOME},
	MissionState.VERIFY_ACTION: {MissionState.RETURN_HOME, MissionState.FAULT},
	MissionState.RETURN_HOME: {MissionState.DONE, MissionState.FAULT},
	MissionState.FAULT: {MissionState.RECOVERY, MissionState.SAFE_MODE},
	MissionState.RECOVERY: {MissionState.BOOT, MissionState.SELF_TEST,
							MissionState.IDLE, MissionState.MISSION,
							MissionState.NAVIGATE, MissionState.SEARCH_TARGET,
							MissionState.APPROACH, MissionState.MANIPULATE,
							MissionState.VERIFY_ACTION, MissionState.RETURN_HOME,
							MissionState.SAFE_MODE},
	MissionState.SAFE_MODE: set(),
	MissionState.DONE: set(),
}

for _state in TRANSITIONS:
	if _state not in {MissionState.SAFE_MODE, MissionState.DONE}:
		TRANSITIONS[_state].add(MissionState.FAULT)


def can_transition(current: MissionState, destination: MissionState) -> bool:
	return destination in TRANSITIONS[current]
