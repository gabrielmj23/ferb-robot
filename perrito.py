import cv2
import time
import imutils
import numpy as np
from collections import deque
from picamera2 import Picamera2
from typing import TYPE_CHECKING
from time import sleep

if TYPE_CHECKING:
    from ferb import Ferb

BUFF_SIZE = 64

# Config colors
blue_lower = (90, 50, 70)
blue_upper = (128, 255, 255)

# --- Configuración de Control del Robot ---
# Estas dimensiones deben coincidir con las usadas en vision_module después del reescalado
# Obtenemos estas dimensiones del vision_module para asegurar consistencia.
# FRAME_WIDTH se usa para calcular FRAME_CENTER_X.
# FRAME_HEIGHT se usa para dibujar en el display.
FRAME_WIDTH = 600 # Usar la constante de vision_module
# FRAME_HEIGHT se obtendrá dinámicamente

FRAME_CENTER_X = FRAME_WIDTH // 2

# Tolerancias y radios objetivo para el control
CENTER_X_TOLERANCE = 80
TARGET_RADIUS_MIN = 70
TARGET_RADIUS_MAX = 100
RADIUS_ADJUST_TOLERANCE = 7

def perrito_mode(robot: "Ferb"):
    """
    Modo perrito
    """
    while True:
        if robot.current_mode != "dog":
            print("Modo perrito detenido.")
            break

        if robot.camera is None:
            print("Error: Cámara no inicializada.")
            continue

        img = robot.camera.capture_array()
        frame = img
        if frame is None:
            print("Error: No se pudo capturar frame de la cámara.")
            continue

        # resize the frame, blur it, and convert it to the HSV
        # color space
        frame = imutils.resize(frame, width=600)
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        # construct a mask for the color blue, then perform
        # a series of dilations and erosions to remove any small
        # blobs left in the mask
        # 
        mask = cv2.inRange(hsv, blue_lower, blue_upper)
        mask = cv2.erode(mask, None, iterations=2)

        # find contours in the mask and initialize the current
        # (x, y) center of the ball
        contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        center = None
        mask = cv2.dilate(mask, None, iterations=2)
        # only proceed if at least one contour was found
        if len(contours) > 0:
            print(f"CONTROL: Se detectó {len(contours)} contornos.")
            # find the largest contour in the mask, then use
            # it to compute the minimum enclosing circle and
            # centroid
            c = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)

            if x and radius:
                error_x = x - FRAME_CENTER_X

                if abs(error_x) > CENTER_X_TOLERANCE:
                    print(f"CONTROL: Pelota a la DERECHA (error {error_x}px). Robot girando IZQUIERDA.")
                    if error_x > 0: # Pelota a la derecha del centro
                        print(f"CONTROL: Pelota a la DERECHA (error {error_x}px). Robot girando IZQUIERDA.")
                        robot.move("left", duration=0.25)
                    else: # Pelota a la izquierda del centro
                        print(f"CONTROL: Pelota a la IZQUIERDA (error {error_x}px). Robot girando DERECHA.")
                        robot.move("right", duration=0.25)
                else:
                    print(f"CONTROL: Centrado en X OK (error {error_x}px).")
                    robot.move("stop")

                # 2. Ajustar la distancia basada en el radio de la pelota
                # Solo ajustar distancia si no se realizó una acción de rotación en este ciclo
                # para evitar movimientos combinados que pueden ser erráticos con "ráfagas".
                if radius < TARGET_RADIUS_MIN - RADIUS_ADJUST_TOLERANCE:
                    print(f"CONTROL: Pelota PEQUEÑA (radio {radius}px). Acercándose.")
                    robot.move("forward", duration=0.75)
                elif radius > TARGET_RADIUS_MAX + RADIUS_ADJUST_TOLERANCE:
                    print(f"CONTROL: Pelota GRANDE (radio {radius}px). Alejándose.")
                    robot.move("backward", duration=0.75)
                else:
                    print(f"CONTROL: Distancia OK (radio {radius}px).")
                    robot.move("stop")
                
                robot.move("stop")

        sleep(0.75)
