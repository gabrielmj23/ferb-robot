import cv2
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from obstaculosDual import capturar_frame_picamera, detectar_obstaculos_dual

if __name__ == "__main__":
    # Abre la webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("No se pudo abrir la webcam")
        sys.exit(1)
    print("Presiona 'q' para salir")
    while True:
        # Captura frame de la webcam
        ret, frame_webcam = cap.read()
        if not ret:
            print("No se pudo capturar frame de la webcam")
            break
        frame_webcam = cv2.cvtColor(frame_webcam, cv2.COLOR_BGR2RGB)
        # Captura frame de la picamera
        try:
            frame_picam = capturar_frame_picamera()
        except Exception as e:
            print(f"Error capturando frame de picamera: {e}")
            break
        # Detecta obstáculos y calcula distancia
        disp_vis, distancia = detectar_obstaculos_dual(frame_picam, frame_webcam)
        cv2.imshow("Disparidad (Stereo)", disp_vis)
        if distancia is not None:
            print(f"Distancia estimada al obstáculo más cercano: {distancia:.1f} cm")
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
