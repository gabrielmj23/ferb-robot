from obstaculos import detectar_obstaculos
import cv2
import time
from time import sleep

# Parámetros de distancia y área para considerar un obstáculo
DISTANCIA_MIN_CM = 30  # Si el obstáculo está más cerca que esto, se evita
MIN_AREA = 2000


def modo_obstaculos(robot):
    """
    Modo de evasión de obstáculos: el robot avanza y esquiva si detecta un obstáculo cerca.
    """
    while True:
        if robot.current_mode != "obstaculos":
            print("Modo obstáculos detenido.")
            break

        if robot.camera is None:
            print("Error: Cámara no inicializada.")
            continue

        frame = robot.camera.capture_array()
        if frame is None:
            print("Error: No se pudo capturar frame de la cámara.")
            continue

        frame, cajas = detectar_obstaculos(frame, min_area=MIN_AREA)
        obstaculo_cerca = False
        for (x, y, w, h), distancia in cajas:
            if distancia is not None and distancia < DISTANCIA_MIN_CM:
                obstaculo_cerca = True
                print(f"Obstáculo detectado a {distancia:.1f} cm. Esquivando...")
                break

        if obstaculo_cerca:
            # Estrategia simple: retroceder y girar
            robot.move("backward", duration=0.5)
            robot.move("left", duration=0.5)
        else:
            print("Camino libre. Avanzando.")
            robot.move("forward", duration=0.5)

        sleep(0.2)
