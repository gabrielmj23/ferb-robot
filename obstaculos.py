import cv2
import numpy as np

# Ajusta estos valores según tu cámara y objeto de referencia
FOCAL_LENGTH_PIXELS = 700  # Estimado, debes calibrar con tu cámara
REAL_OBJECT_HEIGHT_CM = 10  # Altura real del objeto de referencia en cm

def estimar_distancia_caja(caja, focal=FOCAL_LENGTH_PIXELS, real_h=REAL_OBJECT_HEIGHT_CM):
    """
    Estima la distancia al obstáculo usando la altura de la caja.
    """
    _, _, _, h = caja
    if h == 0:
        return None
    distancia = (focal * real_h) / h
    return distancia

def detectar_obstaculos(frame, min_area=2000, aspect_ratio_range=(0.3, 3.0)):
    """
    Detecta obstáculos en la imagen y dibuja cajas alrededor de ellos.
    Retorna la imagen con las cajas y una lista de las cajas encontradas.
    Aplica filtrado morfológico y filtrado por aspecto para mayor precisión.
    """
    # Convertir a escala de grises
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    # Desenfoque para reducir ruido
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    # Umbral simple para detectar objetos oscuros
    _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)
    # Filtrado morfológico para limpiar ruido
    kernel = np.ones((5, 5), np.uint8)
    opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
    # Encontrar contornos
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    resultados = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > min_area:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / float(h) if h != 0 else 0
            if aspect_ratio_range[0] <= aspect_ratio <= aspect_ratio_range[1]:
                distancia = estimar_distancia_caja((x, y, w, h))
                resultados.append(((x, y, w, h), distancia))
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if distancia is not None:
                    cv2.putText(
                        frame,
                        f"{distancia:.1f}cm",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )
    return frame, resultados

def modo_obstaculos(ferb):
    """
    Modo de detección de obstáculos: procesa frames y muestra las cajas.
    """
    print("Modo obstáculos activado")
    while ferb.current_mode == "obstaculos":
        if ferb.camera is None:
            try:
                ferb.start_camera()
            except Exception as e:
                print(f"No se pudo iniciar la cámara: {e}")
                break
        try:
            frame = ferb.camera.capture_array()
            frame, cajas = detectar_obstaculos(frame)
            # Mostrar la imagen con las cajas (solo para debug, quitar en producción)
            cv2.imshow("Obstaculos", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception as e:
            print(f"Error en modo obstaculos: {e}")
            break
    cv2.destroyAllWindows()


