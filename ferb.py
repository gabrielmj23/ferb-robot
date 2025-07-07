from gpiozero import Robot, Motor
import time
from time import sleep
import cv2
from picamera2 import Picamera2
import threading
from perrito import perrito_mode
from gps import GPS
from brujula import Brujula
from modo_obstaculos import modo_obstaculos
from math import radians, sin, cos, sqrt, atan2, degrees
from modo_gestos_control import modo_gestos_control
from collections import deque
from obstaculos import detectar_obstaculos


class Ferb:
    def __init__(
        self, left_motor_pins=(21, 26), right_motor_pins=(0, 25), initial_mode="manual"
    ):
        """
        Setup the robot with the given motor pins.
        """
        self.robot = Robot(
            left=Motor(*left_motor_pins, enable=18),
            right=Motor(*right_motor_pins, enable=27),
        )
        self.current_mode = initial_mode
        self.camera = None
        self.dog_thread_running = False  # Para controlar el hilo del perrito
        self.dog_thread = None
        self.camera_failed = False  # Track camera failure state
        self._continuous_move_thread = None
        self._continuous_move_running = False
        self._continuous_direction = None
        self._continuous_speed = 1
        # gps
        self.gps = GPS()
        self.gps_history_size = 3  # Number of readings to average
        self.gps_position_history = deque(maxlen=self.gps_history_size)
        # brujula
        self.brujula = Brujula(
            i2c_bus=4,
            calibration=Brujula.UCAB_CALIBRATION,
            declination=Brujula.UCAB_DECLINATION,
        )
        # navegacion
        self.obstaculos_thread_running = False  # Para controlar el hilo de obstáculos
        self.obstaculos_thread = None
        self.ruta = []
        # gestos
        self.gestos_thread_running = False  # Para controlar el hilo de gestos
        self.gestos_thread = None

    def _dog_handler(self):
        """
        Private method to handle perrito mode
        """
        while self.dog_thread_running:
            if self.current_mode == "dog":
                print("entro a modo perrito")
                perrito_mode(self)
            sleep(0.5)  # Pequeña pausa para no saturar la CPU

    def start_dog_thread(self):
        """
        Starts the thread that prints "perrito" when current_mode is "dog".
        """
        if not self.dog_thread_running:
            self.dog_thread_running = True
            self.dog_thread = threading.Thread(target=self._dog_handler)
            self.dog_thread.daemon = (
                True  # Hace que el hilo se cierre cuando el programa principal termina
            )
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

    def _obstaculos_handler(self):
        """
        Private method to handle obstaculos mode
        """
        while self.obstaculos_thread_running:
            if self.current_mode == "obstaculos":
                print("entro a modo obstaculos")
                modo_obstaculos(self)
            sleep(0.5)

    def start_obstaculos_thread(self):
        """
        Starts the thread for obstaculos mode.
        """
        if not hasattr(self, 'obstaculos_thread_running') or not self.obstaculos_thread_running:
            self.obstaculos_thread_running = True
            self.obstaculos_thread = threading.Thread(target=self._obstaculos_handler)
            self.obstaculos_thread.daemon = True
            self.obstaculos_thread.start()
            print("Hilo 'obstaculos' iniciado.")

    def stop_obstaculos_thread(self):
        """
        Stops the thread for obstaculos mode.
        """
        if hasattr(self, 'obstaculos_thread_running') and self.obstaculos_thread_running:
            self.obstaculos_thread_running = False
            if self.obstaculos_thread and threading.current_thread() != self.obstaculos_thread:
                self.obstaculos_thread.join()
            print("Hilo 'obstaculos' detenido.")

    def _gestos_handler(self):
        """
        Private method to handle gestos mode
        """
        while self.gestos_thread_running:
            if self.current_mode == "gestos":
                print("entro a modo gestos")
                modo_gestos_control(self)
            sleep(0.5)

    def start_gestos_thread(self):
        """
        Starts the thread for gestos mode.
        """
        if not hasattr(self, 'gestos_thread_running') or not self.gestos_thread_running:
            self.gestos_thread_running = True
            self.gestos_thread = threading.Thread(target=self._gestos_handler)
            self.gestos_thread.daemon = True
            self.gestos_thread.start()
            print("Hilo 'gestos' iniciado.")

    def stop_gestos_thread(self):
        """
        Stops the thread for gestos mode.
        """
        if hasattr(self, 'gestos_thread_running') and self.gestos_thread_running:
            self.gestos_thread_running = False
            if self.gestos_thread and threading.current_thread() != self.gestos_thread:
                self.gestos_thread.join()
            print("Hilo 'gestos' detenido.")

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
                        raw={"size": (820, 616)},
                        main={"format": "RGB888", "size": (320, 240)},
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
            cv2.putText(
                img,
                "Camera error",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                2,
                (0, 0, 255),
                3,
            )
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
        self.stop_dog_thread()  # Asegúrate de detener el hilo del perrito al limpiar
        self.stop_obstaculos_thread()  # Detén el hilo de obstáculos también
        self.stop_gestos_thread()  # Detén el hilo de gestos también
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
            self._continuous_move_thread = threading.Thread(
                target=self._continuous_move_worker
            )
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

    def move(
        self,
        direction: str,
        speed: float = 1.0,
        continuous: bool = False,
        duration: float = 1,
    ):
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

            sleep(1)

    def compass_stream(self):
        """
        Generator que produce la dirección de la brújula.
        """
        while True:
            bearing = self.brujula.sensor.get_bearing()
            if bearing is not None:
                yield f"data: {bearing:.2f}\n\n"
            else:
                yield "data: Error al obtener la dirección de la brújula.\n\n"
            sleep(0.25)

    def start_navigation(self, ruta):
        """
        Inicia la navegación especificando una ruta.
        """
        print("Iniciando navegación con la ruta:", ruta)
        self.ruta = ruta
        self.navigate()

    def haversine(self, lat1, lon1, lat2, lon2):
        """
        Calcula la distancia en metros entre dos coordenadas GPS.
        """
        R = 6371000  # Radio de la Tierra en metros
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def bearing_to(self, lat1, lon1, lat2, lon2):
        """
        Calcula el rumbo (en grados) del punto actual al objetivo.
        """
        lat1 = radians(lat1)
        lat2 = radians(lat2)
        dlon = radians(lon2 - lon1)
        x = sin(dlon) * cos(lat2)
        y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
        initial_bearing = atan2(x, y)
        initial_bearing = degrees(initial_bearing)
        compass_bearing = (initial_bearing + 360) % 360
        return compass_bearing

    def get_current_position(self):
        """
        Lee la posición actual del GPS (lat, lon) y aplica promediado para mitigar el drift.
        Devuelve None si no hay fix válido o si no hay suficientes datos para promediar.
        """
        raw_data = self.gps.read_data()
        
        if isinstance(raw_data, dict) and raw_data.get("lat", None) is not None and raw_data.get("lon", None) is not None:
            current_lat = float(raw_data["lat"])
            current_lon = float(raw_data["lon"])
            
            # Add current valid reading to history
            self.gps_position_history.append((current_lat, current_lon))
            
            # Only average if we have enough readings
            if len(self.gps_position_history) == self.gps_history_size:
                avg_lat = sum(p[0] for p in self.gps_position_history) / self.gps_history_size
                avg_lon = sum(p[1] for p in self.gps_position_history) / self.gps_history_size
                return avg_lat, avg_lon
            else:
                # Not enough data yet, return the latest valid reading or wait
                # For this implementation, we'll return None until buffer is full.
                # You could also return the raw_data here if you want faster updates,
                # but with less smoothing.
                print(f"GPS: Acumulando datos ({len(self.gps_position_history)}/{self.gps_history_size})...")
                return None
        else:
            # Clear history if no valid fix to avoid averaging stale data
            # if len(self.gps_position_history) > 0:
            #     print("GPS: Sin fix válido, limpiando historial de GPS.")
            #     self.gps_position_history.clear()
            return None

    def get_current_heading(self):
        """
        Obtiene el heading actual de la brújula.
        """
        return self.brujula.sensor.get_bearing()

    def turn_to_heading(self, target_heading, tolerance=5):
        """
        Gira el robot hasta que el heading esté dentro del tolerance (grados).
        """
        while True:
            current_heading = self.get_current_heading()
            if current_heading is None:
                sleep(0.1)
                continue
            diff = (target_heading - current_heading + 360) % 360
            if diff < tolerance or diff > 360 - tolerance:
                self.robot.stop()
                break
            elif diff < 180:
                self.robot.right(speed=0.5)
            else:
                self.robot.left(speed=0.5)
            sleep(0.1)
        self.robot.stop()

    def navigate(self, threshold=1.5, avance_time=5):
        """
        Navega a través de la ruta especificada (self.ruta).
        threshold: distancia en metros para considerar que llegó al punto.
        avance_time: tiempo en segundos para avanzar antes de volver a chequear.
        """
        # Parámetros para la evasión de obstáculos
        DISTANCIA_MIN_CM = 30
        MIN_AREA = 2000

        if not self.ruta:
            raise ValueError("No hay ruta definida para navegar.")
        for idx, punto in enumerate(self.ruta):
            target_lat = punto.lat
            target_lon = punto.lng
            while True:
                pos = self.get_current_position()
                if not pos:
                    print("Esperando señal GPS...")
                    sleep(1)
                    continue
                lat, lon = pos
                self.gps_position_history.clear()
                dist = self.haversine(lat, lon, target_lat, target_lon)
                print(f"Punto {idx+1}/{len(self.ruta)}: Distancia al objetivo: {dist:.2f} m")
                if dist < threshold:
                    print(f"Punto {idx+1} alcanzado.")
                    self.robot.stop()
                    break
                bearing = self.bearing_to(lat, lon, target_lat, target_lon)
                print(f"Rumbo objetivo: {bearing:.2f}°")
                self.turn_to_heading(bearing)
                print(f"Avanzando {avance_time} segundos...")
                start_time = time.time()
                # Bucle de avance con detección de obstáculos
                while time.time() - start_time < avance_time:
                    frame = self.camera.capture_array()
                    _, cajas = detectar_obstaculos(frame, min_area=MIN_AREA)
                    
                    obstaculo_cerca = any(
                        dist is not None and dist < DISTANCIA_MIN_CM for _, dist in cajas
                    )

                    if obstaculo_cerca:
                        # Gira hasta que el camino esté libre o se agoten los intentos
                        max_intentos_giro = 25  # Aprox. 5 seg de giro (25 * 0.2s)
                        for intento in range(max_intentos_giro):
                            self.robot.left(speed=0.6)
                            sleep(0.2)
                            
                            frame_nuevo = self.camera.capture_array()
                            if frame_nuevo is None: continue
                            
                            _, cajas_nuevas = detectar_obstaculos(frame_nuevo, min_area=MIN_AREA)
                            if not any(d is not None and d < DISTANCIA_MIN_CM for _, d in cajas_nuevas):
                                self.robot.stop()
                                print("✅ Camino despejado. Reanudando avance.")
                                break # Sale del bucle de giro
                        else:
                            # Este 'else' se ejecuta si el 'for' termina sin 'break'
                            self.robot.stop()
                            print("⚠️ No se encontró un camino libre. Forzando recalculo de GPS.")
                            # Rompe el bucle de avance_time para forzar un recalculo
                            break 
                    else:
                        self.robot.forward(speed=1)
                        sleep(0.2)
                self.robot.stop()
                print("Reevaluando posición...")
        print("Ruta completada.")
        self.ruta = []


