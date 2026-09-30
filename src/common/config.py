# --- Perception— calibrer avec tools/calibrate_color.py -----------

# Bornes HSV de la cible (valeurs par défaut : jaune/orange, comme Adeept).
TARGET_HSV_LOW  = (24, 100, 100)
TARGET_HSV_HIGH = (44, 255, 255)

# Aire minimale du contour pour valider une détection (bruit de fond).
TARGET_MIN_AREA_PX = 300

# Calibration du rayon apparent : pose la cible à CALIB_DISTANCE_M mètres,
# relève son radius_px avec tools/calibrate_color.py, recopie-le ici.
CALIB_DISTANCE_M = 0.50
CALIB_RADIUS_PX  = 60.0

# Aire du contour quand la cible est vue à ~1 m (saturation de la confiance).
TARGET_REF_AREA_PX = 1500

# --- Ultrason / obstacles ----------------------------------------------------
OBSTACLE_STOP_M          = 0.30   # plus proche → il FAUT s'arrêter
OBSTACLE_WARN_M          = 0.60   # plus proche → obstacle détecté (alerte)
ULTRASONIC_MIN_VALID_M   = 0.02   # en dessous : lecture impossible → invalide
ULTRASONIC_MAX_VALID_M   = 4.00   # au delà : hors de portée fiable → invalide