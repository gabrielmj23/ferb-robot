import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Índices de los puntos de referencia de los dedos
FINGER_TIPS = [4, 8, 12, 16, 20]  # Pulgar, índice, medio, anular, meñique
FINGER_PIPS = [2, 6, 10, 14, 18]  # Articulaciones intermedias


def dedos_extendidos(hand_landmarks):
    """
    Recibe landmarks de una mano y retorna una lista booleana indicando si cada dedo está extendido.
    [pulgar, índice, medio, anular, meñique]
    """
    dedos = []
    # Pulgar: comparar x (horizontal) porque la mano puede estar rotada
    if hand_landmarks.landmark[FINGER_TIPS[0]].x > hand_landmarks.landmark[FINGER_PIPS[0]].x:
        dedos.append(True)
    else:
        dedos.append(False)
    # Otros dedos: comparar y (vertical)
    for tip, pip in zip(FINGER_TIPS[1:], FINGER_PIPS[1:]):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            dedos.append(True)
        else:
            dedos.append(False)
    return dedos


def modo_gestos(robot):
    """
    Modo de gestos: procesa frames y detecta qué dedos están extendidos usando MediaPipe.
    """
    with mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.9) as hands:
        while True:
            if robot.current_mode != "gestos":
                print("Modo gestos detenido.")
                break
            if robot.camera is None:
                print("Error: Cámara no inicializada.")
                continue
            frame = robot.camera.capture_array()
            if frame is None:
                print("Error: No se pudo capturar frame de la cámara.")
                continue
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    dedos = dedos_extendidos(hand_landmarks)
                    print(f"Dedos extendidos: {dedos} (Pulgar, Índice, Medio, Anular, Meñique)")
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            cv2.imshow("Gestos - MediaPipe", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()
