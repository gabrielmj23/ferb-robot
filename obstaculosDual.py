import cv2
import numpy as np
from picamera2 import Picamera2

# Ajusta estos valores según tu cámara y objeto de referencia
FOCAL_LENGTH_PIXELS = 700  # Estimado, debes calibrar con tu cámara
REAL_OBJECT_HEIGHT_CM = 10  # Altura real del objeto de referencia en cm


def estimar_distancia_disparidad(disparidad, baseline_cm, focal_px):
    """
    Calcula la distancia usando la disparidad, baseline (distancia entre cámaras) y la focal.
    """
    if disparidad <= 0:
        return None
    return (baseline_cm * focal_px) / disparidad


def capturar_frame_picamera():
    """
    Captura un frame de la cámara Raspberry Pi (Picamera2).
    """
    picam = Picamera2()
    picam.configure(
        picam.create_preview_configuration(
            raw={"size": (1640, 1232)},
            main={"format": "RGB888", "size": (640, 480)},
        )
    )
    picam.start()
    import time
    time.sleep(2)
    frame = picam.capture_array()
    picam.close()
    return frame


def detectar_obstaculos_dual(frame1, frame2, baseline_cm=6.0, focal_px=FOCAL_LENGTH_PIXELS):
    """
    Detecta obstáculos usando dos cámaras (frame1: picamera, frame2: webcam).
    Retorna el mapa de disparidad y la distancia estimada al obstáculo más cercano.
    """
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2GRAY)
    # Usar StereoBM para calcular disparidad
    stereo = cv2.StereoBM_create(numDisparities=64, blockSize=15)
    disparity = stereo.compute(gray1, gray2).astype(np.float32) / 16.0
    # Normalizar para visualización
    disp_vis = cv2.normalize(disparity, None, 0, 255, cv2.NORM_MINMAX)
    disp_vis = np.uint8(disp_vis)
    # Buscar la disparidad mínima (mayor profundidad)
    min_disp = np.min(disparity[disparity > 0]) if np.any(disparity > 0) else 0
    distancia = estimar_distancia_disparidad(min_disp, baseline_cm, focal_px) if min_disp > 0 else None
    return disp_vis, distancia
