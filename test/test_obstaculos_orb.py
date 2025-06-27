import cv2
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from obstaculosORB import detectar_obstaculos_orb


if __name__ == "__main__":
    # Permite probar con una imagen o con la webcam
    if len(sys.argv) > 1:
        # Prueba con una imagen
        img_path = sys.argv[1]
        frame = cv2.imread(img_path)
        if frame is None:
            print(f"No se pudo cargar la imagen: {img_path}")
            sys.exit(1)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_kp, distancia, kp = detectar_obstaculos_orb(frame)
        print(f"Keypoints detectados: {len(kp)}")
        if distancia is not None:
            print(f"Distancia estimada: {distancia:.1f} cm")
        cv2.imshow("ORB Keypoints", cv2.cvtColor(frame_kp, cv2.COLOR_RGB2BGR))
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        # Prueba con webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("No se pudo abrir la cámara")
            sys.exit(1)
        while True:
            ret, frame = cap.read()
            if not ret:
                print("No se pudo capturar frame")
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_kp, distancia, kp = detectar_obstaculos_orb(frame)
            cv2.imshow("ORB Keypoints", cv2.cvtColor(frame_kp, cv2.COLOR_RGB2BGR))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
