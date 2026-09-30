"""Test bout-en-bout de la chaîne perception — Definition of Done du Jour 1.

Usage (depuis la racine du projet) :
    python3 -m tools.perception_test
    python3 -m tools.perception_test --no-ultrasonic

Critères de succès :
    - une ligne par frame : TARGET ... | OBSTACLE ... | lat=...
    - frames annotées sauvées dans logs/perception_test/ (matière vidéo démo)
    - aucun crash pendant ~2 minutes, y compris en éloignant/rapprochant la cible
"""
import time
from pathlib import Path

import cv2

from src.common.logger import EventLogger
from src.common.types import PerceptionResult
from src.hardware.picar_camera import PicarCamera
from src.perception.perception_service import PerceptionService

OUT = Path("logs/perception_test")


def fmt(r: PerceptionResult) -> str:
    t, o = r.target, r.obstacle
    tgt = (f"TARGET found | x={t.x:+.2f} | d={t.distance_m:.2f} m | conf={t.confidence:.2f}"
           if t.found else "TARGET none")
    obs = f"OBSTACLE d={o.distance_m:.2f} m" if o.valid else "OBSTACLE invalid"
    return f"{tgt:48s} | {obs:22s} | lat={r.latency_ms:.1f} ms"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ultrasonic", action="store_true",
                    help="tester la caméra seule (ultrason pas encore branché)")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    log = EventLogger("perception_test")

    cam = PicarCamera()
    log.info(f"camera ok, warm-up done, fps={cam.fps:.1f}")

    sensor = None
    if not args.no_ultrasonic:
        from src.hardware.ultrasonic import UltrasonicSensor
        sensor = UltrasonicSensor()
        log.info("ultrasonic ok")

    perception = PerceptionService()
    n = 0
    try:
        while True:
            frame = cam.read()
            distance = None
            if sensor is not None:
                try:
                    distance = sensor.read_distance_m()
                except Exception as exc:      # capteur muet : on continue en dégradé
                    log.warn(f"ultrasonic: {exc}")
                    distance = None

            result = perception.process(frame, distance)
            print(fmt(result))

            if result.target.found and n % 10 == 0:
                ann = perception.target.annotate(frame.image, result.target)
                cv2.imwrite(str(OUT / f"frame_{n:04d}.jpg"), ann)
            n += 1
            time.sleep(0.05)
    except KeyboardInterrupt:
        log.info(f"stopped after {n} frames")
    finally:
        cam.release()
        if sensor:
            sensor.cleanup()
        log.close()


if __name__ == "__main__":
    main()