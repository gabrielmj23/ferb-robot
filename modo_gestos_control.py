import cv2
import mediapipe as mp
from gestos import dedos_extendidos
from time import sleep

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


def modo_gestos_control(robot):
    """
    Modo de gestos con control: mueve el robot según el gesto detectado.
    Usa la picamera (robot.camera.capture_array()).
    """
    with mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.5) as hands:
        while True:
            if robot.current_mode != "gestos":
                print("Modo gestos control detenido.")
                break
            if robot.camera is None:
                print("Error: Cámara no inicializada.")
                continue
            frame = robot.camera.capture_array()
            if frame is None:
                print("Error: No se pudo capturar frame de la cámara.")
                continue
            # Picamera2 entrega RGB, convertir a BGR para mostrar y a RGB para MediaPipe
            frame_rgb = frame if frame.shape[2] == 3 else cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)
            accion = None
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    dedos = dedos_extendidos(hand_landmarks)
                    # Lógica de control
                    if dedos == [False, False, False, False, False]:
                        accion = "forward"
                        print("Gesto: Puño - Avanzar")
                    elif dedos == [True, True, True, True, True]:
                        accion = "backward"
                        print("Gesto: Mano abierta - Retroceder")
                    elif dedos == [False, True, False, False, False]:
                        accion = "right"
                        print("Gesto: Solo índice - Derecha")
                    elif dedos == [False, True, True, False, False]:
                        accion = "left"
                        print("Gesto: Índice y medio - Izquierda")
                    elif dedos == [False, False, True, False, False]:
                        accion = "spin"
                        print("Gesto: Solo medio - Giro")
                    else:
                        accion = "stop"
                        print("Gesto: Otro - Stop")
                    # Ejecutar acción
                    if accion == "forward":
                        robot.move("forward", duration=0.5)
                    elif accion == "backward":
                        robot.move("backward", duration=0.5)
                    elif accion == "right":
                        robot.move("right", duration=0.5)
                    elif accion == "left":
                        robot.move("left", duration=0.5)
                    elif accion == "spin":
                        robot.move("right", duration=0.5)
                        robot.move("right", duration=0.5)
                    else:
                        robot.move("stop")
                    # Mostrar landmarks sobre frame BGR
                    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                    mp_drawing.draw_landmarks(frame_bgr, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    cv2.imshow("Gestos Control - MediaPipe", frame_bgr)
            else:
                # Si no hay mano, mostrar frame normal
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                cv2.imshow("Gestos Control - MediaPipe", frame_bgr)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            sleep(0.2)
        cv2.destroyAllWindows()
