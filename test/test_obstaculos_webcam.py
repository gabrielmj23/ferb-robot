import cv2
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from obstaculos import detectar_obstaculos

def main():
    cap = cv2.VideoCapture(0) #Webcam
    if not cap.isOpened():
        print("No se pudo abrir la webcam")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("No se pudo leer el frame de la webcam")
            break

        # OpenCV usa BGR pero la funcion usa RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_out, cajas = detectar_obstaculos(frame_rgb)

        # Volver a BGR para mostrar
        frame_show = cv2.cvtColor(frame_out, cv2.COLOR_RGB2BGR)
        cv2.imshow("Detección de Obstáculos", frame_show)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()