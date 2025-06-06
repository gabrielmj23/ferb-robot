from gpiozero import Robot, Motor
from time import sleep
import cv2
from picamera2 import Picamera2
import threading
from perrito import perrito_mode
from gps import GPS

class Ferb:
    def __init__(
        self, left_motor_pins=(26, 21), right_motor_pins=(0, 25), initial_mode="manual"
    ):
        """
        Setup the robot with the given motor pins.
        """
        self.robot = Robot(left=Motor(*left_motor_pins, enable=18), right=Motor(*right_motor_pins, enable=27))
        self.current_mode = initial_mode
        self.camera = None
        self.dog_thread_running = False # Para controlar el hilo del perrito
        self.dog_thread = None
        self.camera_failed = False  # Track camera failure state
        self._continuous_move_thread = None
        self._continuous_move_running = False
        self._continuous_direction = None
        self._continuous_speed = 1
        self.gps = GPS()

    def _dog_handler(self):
        """
        Private method to handle perrito mode
        """
        while self.dog_thread_running:
            if self.current_mode == "dog":
                print("entro a modo perrito")
                perrito_mode(self)
            sleep(0.5) # Pequeña pausa para no saturar la CPU

    def start_dog_thread(self):
        """
        Starts the thread that prints "perrito" when current_mode is "dog".
        """
        if not self.dog_thread_running:
            self.dog_thread_running = True
            self.dog_thread = threading.Thread(target=self._dog_handler)
            self.dog_thread.daemon = True # Hace que el hilo se cierre cuando el programa principal termina
            self.dog_thread.start()
            print("Hilo 'perrito' iniciado.")

    def stop_dog_thread(self):
        """
        Stops the thread that prints "perrito".
        """
        if self.dog_thread_running:
            self.dog_thread_running = False
            if self.dog_thread and threading.current_thread() != self.dog_thread:
                self.dog_thread.join()  # Espera a que el hilo termine su ejecución actual
            print("Hilo 'perrito' detenido.")


    def start_camera(self, camera_index=0):
        """
        Initialize the camera.
        """
        if self.camera_failed:
            print("Camera previously failed to initialize. Skipping re-initialization.")
            raise RuntimeError("Camera is in a failed state.")
        if self.camera is None:
            try:
                self.camera = Picamera2()
                self.camera.configure(
                    self.camera.create_preview_configuration(
                        raw={"size":(1640,1232)}, main={"format":"RGB888", "size": (640,480)}
                    )
                )
                self.camera.start()
                sleep(2)
            except Exception as e:
                print(f"Error initializing camera: {e}")
                # Picamera2 may leave a broken object and background thread after failure.
                # This is a known issue and cannot be fully avoided in user code.
                self.stop_camera()  # Ensure cleanup
                try:
                    del self.camera
                except Exception:
                    pass
                self.camera = None
                self.camera_failed = True
                raise

    def stop_camera(self):
        """
        Release the camera resource.
        """
        if self.camera is not None:
            try:
                self.camera.close()
            except Exception as e:
                print(f"Error releasing camera: {e}")
            self.camera = None
        self.camera_failed = False  # Allow future attempts after explicit stop

    def camera_stream(self):
        """
        Generator that yields camera frames as JPEG for streaming.
        """
        try:
            self.start_camera()
        except Exception as e:
            # Yield a single frame with an error message as JPEG
            import numpy as np
            img = np.zeros((100, 480, 3), dtype=np.uint8)
            cv2.putText(img, "Camera error", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 3)
            ret, jpeg = cv2.imencode(".jpg", img)
            if ret:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
                )
            return
        while True:
            if self.camera is None:
                break
            try:
                img = self.camera.capture_array()
                ret, jpeg = cv2.imencode(".jpg", img)
                if not ret:
                    continue
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
                )
            except Exception as e:
                print(f"Camera streaming error: {e}")
                self.stop_camera()
                break

    def cleanup(self):
        """
        Cleanup the robot resources.
        """
        self.stop_dog_thread() # Asegúrate de detener el hilo del perrito al limpiar
        self.stop_camera()
        self.robot.close()

    def _continuous_move_worker(self):
        """
        Mantiene el robot moviéndose en la dirección indicada hasta que se cambie o se detenga.
        """
        while self._continuous_move_running:
            direction = self._continuous_direction
            speed = self._continuous_speed
            if direction == "forward":
                self.robot.forward(speed)
            elif direction == "backward":
                self.robot.backward(speed)
            elif direction == "left":
                self.robot.left(speed)
            elif direction == "right":
                self.robot.right(speed)
            elif direction == "stop" or direction is None:
                self.robot.stop()
            # Repite cada 0.2 segundos para mantener el movimiento
            sleep(0.2)

    def start_continuous_move(self, direction, speed=1):
        """
        Inicia el movimiento continuo en la dirección dada.
        """
        self.stop_continuous_move()
        self._continuous_direction = direction
        self._continuous_speed = speed
        if direction != "stop":
            self._continuous_move_running = True
            self._continuous_move_thread = threading.Thread(target=self._continuous_move_worker)
            self._continuous_move_thread.daemon = True
            self._continuous_move_thread.start()

    def stop_continuous_move(self):
        """
        Detiene el movimiento continuo.
        """
        self._continuous_move_running = False
        if self._continuous_move_thread:
            self._continuous_move_thread.join(timeout=1)
        self._continuous_move_thread = None
        self._continuous_direction = None
        self.robot.stop()

    def move(self, direction: str, speed: float = 1.0, continuous: bool = False, duration: float = 1):
        """
        Handle movement.
        Si continuous=True, mantiene el movimiento hasta que se mande otra dirección o stop.
        Si continuous=False, solo mueve una vez (como en el index.html).
        """
        print("Current mode:", self.current_mode)
        print("Direction:", direction)
        print("Speed:", speed)
        if continuous:
            if direction == "stop":
                self.stop_continuous_move()
            else:
                self.start_continuous_move(direction, speed)
        else:
            self.stop_continuous_move()  # Detén cualquier movimiento continuo previo
            if direction == "forward":
                print("Moving forward")
                self.robot.forward(speed)
                sleep(duration)
            elif direction == "backward":
                self.robot.backward(speed)
                sleep(duration)
            elif direction == "left":
                self.robot.left(speed)
                sleep(duration)
            elif direction == "right":
                self.robot.right(speed)
                sleep(duration)
            else:
                self.robot.stop()

    def gps_stream(self):
        """
        Generator que produce solo latitud y longitud, o un mensaje si no hay fix.
        """
        while True:
            data = self.gps.read_data()
            lat = None
            lon = None
            # Intenta extraer latitud y longitud del objeto data
            if data:
                # Si data es un dict o tiene atributos lat/lon
                if isinstance(data, dict):
                    lat = data.get("lat") or data.get("latitude")
                    lon = data.get("lon") or data.get("longitude")
                else:
                    lat = getattr(data, "lat", None) or getattr(data, "latitude", None)
                    lon = getattr(data, "lon", None) or getattr(data, "longitude", None)
            if lat is not None and lon is not None:
                yield f"data: {lat},{lon}\n\n"
            else:
                yield "data: El GPS no se ha posicionado. Muévase a un sitio más despejado.\n\n"
            import time
            time.sleep(1)
