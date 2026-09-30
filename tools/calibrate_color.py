"""Calibration HSV de la cible + calibration du rayon apparent.

1. Pose la cible à une distance connue (ex. 0.50 m), vise-la.
2. Ajuste les trackbars jusqu'à ce que la fenêtre 'mask' montre la cible
   en blanc plein sur fond noir.
3. Recopie les valeurs LOW/HIGH affichées dans src/common/config.py
   (TARGET_HSV_LOW / TARGET_HSV_HIGH).
4. Note le radius_px affiché → CALIB_RADIUS_PX, avec CALIB_DISTANCE_M = ta
   distance de calibration.
5. Note l'area affichée vue à ~1 m → TARGET_REF_AREA_PX.

'q' pour quitter (récapitulatif imprimé).
"""
import cv2
import numpy as np

from src.hardware.picar_camera import PicarCamera


def nothing(_):
    pass


def main():
    cam = PicarCamera()
    cv2.namedWindow("calib", cv2.WINDOW_NORMAL)
    for name, default in [("H-", 24), ("S-", 100), ("V-", 100),
                          ("H+", 44), ("S+", 255), ("V+", 255)]:
        cv2.createTrackbar(name, "calib", default, 255, nothing)

    while True:
        frame = cam.read()
        img = frame.image
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        low = np.array([cv2.getTrackbarPos("H-", "calib"),
                        cv2.getTrackbarPos("S-", "calib"),
                        cv2.getTrackbarPos("V-", "calib")])
        high = np.array([cv2.getTrackbarPos("H+", "calib"),
                         cv2.getTrackbarPos("S+", "calib"),
                         cv2.getTrackbarPos("V+", "calib")])
        mask = cv2.inRange(hsv, low, high)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        info = f"LOW={low.tolist()} HIGH={high.tolist()}"
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)[-2]
        if cnts:
            c = max(cnts, key=cv2.contourArea)
            (_, _), r = cv2.minEnclosingCircle(c)
            info += f"  area={int(cv2.contourArea(c))} radius_px={r:.0f}"
            cv2.drawContours(img, [c], -1, (0, 255, 0), 2)

        cv2.putText(img, info, (10, 470), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (255, 255, 255), 1)
        cv2.imshow("calib", img)
        cv2.imshow("mask", mask)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("\nRecopie dans src/common/config.py :")
            print(f"TARGET_HSV_LOW  = {low.tolist()}")
            print(f"TARGET_HSV_HIGH = {high.tolist()}")
            break

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()