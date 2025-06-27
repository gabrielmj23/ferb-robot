import cv2
import numpy as np

# Ajusta estos valores según tu cámara y objeto de referencia
FOCAL_LENGTH_PIXELS = 700  # Estimado, debes calibrar con tu cámara
REAL_OBJECT_HEIGHT_CM = 10  # Altura real del objeto de referencia en cm


def estimar_distancia_keypoints(kp, focal=FOCAL_LENGTH_PIXELS, real_h=REAL_OBJECT_HEIGHT_CM):
    """
    Estima la distancia a un obstáculo usando la dispersión vertical de los keypoints detectados.
    """
    if len(kp) < 2:
        return None
    # Tomar la diferencia máxima de y entre keypoints (altura en pixeles)
    ys = [p.pt[1] for p in kp]
    h = max(ys) - min(ys)
    if h == 0:
        return None
    distancia = (focal * real_h) / h
    return distancia


def detectar_obstaculos_orb(frame, min_keypoints=10):
    """
    Detecta obstáculos usando puntos clave ORB, dibuja los keypoints y estima la distancia.
    Retorna la imagen con los keypoints y la distancia estimada.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    orb = cv2.ORB_create(nfeatures=500)
    kp = orb.detect(gray, None)
    kp, des = orb.compute(gray, kp)
    frame_kp = cv2.drawKeypoints(frame, kp, None, color=(0, 255, 0), flags=0)
    distancia = None
    if kp and len(kp) >= min_keypoints:
        distancia = estimar_distancia_keypoints(kp)
        if distancia is not None:
            cv2.putText(
                frame_kp,
                f"Distancia aprox: {distancia:.1f}cm",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
    return frame_kp, distancia, kp


def modo_obstaculos_orb(ferb):
    """
    Modo de detección de obstáculos usando ORB: procesa frames y muestra los keypoints.
    """
    print("Modo obstáculos ORB activado")
    while ferb.current_mode == "obstaculos_orb":
        if ferb.camera is None:
            try:
                ferb.start_camera()
            except Exception as e:
                print(f"No se pudo iniciar la cámara: {e}")
                break
        try:
            frame = ferb.camera.capture_array()
            frame_kp, distancia, kp = detectar_obstaculos_orb(frame)
            cv2.imshow("Obstaculos ORB", cv2.cvtColor(frame_kp, cv2.COLOR_RGB2BGR))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception as e:
            print(f"Error en modo obstaculos ORB: {e}")
            break
    cv2.destroyAllWindows()
