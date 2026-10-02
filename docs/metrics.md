# Metrics and Measurement Plan

## Software Test Results

| Metric | Result | Interpretation |
|---|---:|---|
| Baseline automated suite | 20 passed | Prior to Day 4 verification additions |
| Updated focused suite | 21 passed | Navigation, mission, FDIR, and observability; manipulator tests excluded |
| Final full suite | 24 passed | Full `unittest` discovery after Day 4 test additions |

These are test counts, not rover performance metrics.

## Physical Campaign

| Metric | Definition | Collection method | Status |
|---|---|---|---|
| Mission completion rate | Successful runs / total runs | Record `SUCCESS`, `ABORTED`, or `SAFE` per controlled run | NOT RUN |
| Mission duration | Mission start to terminal outcome | Timestamp start and outcome logs | NOT RUN |
| Target detection rate | Correct detections / labeled target frames | Labeled camera trials | NOT RUN |
| False-positive rate | Incorrect detections / labeled negative frames | Labeled negative scenes | NOT RUN |
| Perception latency | Distribution of `PerceptionResult.latency_ms` | Collect per-frame values on Pi | NOT RUN |
| CPU/RAM/temperature | Platform telemetry during a run | Sample Adeept `Info` adapter | NOT RUN |
| Control-loop period | Time between navigation steps | Timestamp consecutive loop iterations | NOT RUN |
| Fault detection/recovery time | Detection-to-response and retry-to-decision time | Timestamp fault and recovery events | NOT RUN |
| Recovery success rate | Verified recoveries / recovery attempts | Repeatable recoverable-fault campaign | NOT RUN |
| Collision rate / return error | Collisions or distance from start on return | Instrumented course and external measurements | NOT RUN |

Do not infer physical metrics from unit tests. Motor response, battery percentage, distance traveled, and collision ground truth are not instrumented.