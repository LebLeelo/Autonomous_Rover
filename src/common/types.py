"""Types abstraits partagés. Aucune dépendance hardware ici."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import numpy as np


@dataclass
class Frame:
    """Une image BGR + son timestamp (temps de capture réel)."""
    image: np.ndarray
    timestamp: float


@dataclass
class Detection:
    """Cible vue par la caméra.

    x, y : normalisés -1..+1 (0 = centre de l'image). -1 = bord gauche.
    distance_m : estimation par rayon apparent, None si indisponible.
    confidence : 0..1 (aire du contour vs aire de référence calibrée).
    """
    found: bool = False
    x: float = 0.0
    y: float = 0.0
    radius_px: float = 0.0
    distance_m: Optional[float] = None
    confidence: float = 0.0


@dataclass
class Obstacle:
    """Obstacle devant le rover.

    valid=False : lecture capteur INVALIDE (range check) → à rejeter,
    ne doit JAMAIS déclencher une décision.
    detected=True : distance <= seuil d'alerte.
    """
    valid: bool = False
    detected: bool = False
    distance_m: Optional[float] = None
    direction: str = "FRONT"   # capteur unique, fixe, orienté avant


@dataclass
class PerceptionResult:
    """Sortie unique du composant Perception, consommée par la Navigation."""
    target: Detection
    obstacle: Obstacle
    latency_ms: float = 0.0