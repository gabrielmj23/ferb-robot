from gpiozero import Robot, Motor
import gpiod
from time import sleep
import cv2
from picamera2 import Picamera2
import threading
from perrito import perrito_mode

# Pines para el Motor Izquierdo
MOTOR_LEFT_FORWARD_PIN = 18    # GPIO 17 -> L298N IN1
MOTOR_LEFT_BACKWARD_PIN = 17   # GPIO 18 -> L298N IN2
MOTOR_LEFT_ENA_PIN = 12        # GPIO 12 -> L298N ENA (Enable Motor A)

# Pines para el Motor Derecho
MOTOR_RIGHT_FORWARD_PIN = 27   # GPIO 27 -> L298N IN3
MOTOR_RIGHT_BACKWARD_PIN = 22  # GPIO 22 -> L298N IN4
MOTOR_RIGHT_ENB_PIN = 13       # GPIO 13 -> L298N ENB (Enable Motor B)

class Ferb:
    def __init__(
        self, left_motor_pins=(18, 17), right_motor_pins=(22, 27), initial_mode="manual"
    ):
        """
        Setup the robot with the given motor pins.
        """
        self.chip = gpiod.Chip("gpiochip0")
        self.lines = {
            "left_forward": self.chip.get_line(MOTOR_LEFT_FORWARD_PIN),
            "left_backward": self.chip.get_line(MOTOR_LEFT_BACKWARD_PIN),
            "left_ena": self.chip.get_line(MOTOR_LEFT_ENA_PIN),
            "right_forward": self.chip.get_line(MOTOR_RIGHT_FORWARD_PIN),
            "right_backward": self.chip.get_line(MOTOR_RIGHT_BACKWARD_PIN),
            "right_enb": self.chip.get_line(MOTOR_RIGHT_ENB_PIN),
            "chip": self.chip # Guardamos el chip para poder cerrarlo en finally
        }
        for name, line_obj in self.lines.items():
            if name != "chip": # No solicitar el chip mismo
                line_obj.request(consumer=f"motor_{name}", type=gpiod.LINE_REQ_DIR_OUT)
                # Asegurarse de que estén apagadas al inicio
                line_obj.set_value(0)

        # self.robot = Robot(left=Motor(*left_motor_pins, enable=12), right=Motor(*right_motor_pins, enable=13))
        self.current_mode = initial_mode
        self.camera = None
        self.dog_thread_running = False # Para controlar el hilo del perrito
        self.dog_thread = None
        self.camera_failed = False  # Track camera failure state
        self._continuous_move_thread = None
        self._continuous_move_running = False
        self._continuous_direction = None
        self._continuous_speed = 1

    def _set_motor_direction(self, forward_line, backward_line, forward_state, backward_state):
        """Función interna para establecer la dirección de un motor."""
        forward_line.set_value(forward_state)
        backward_line.set_value(backward_state)

    def _enable_motor(self, ena_line, enable=True):
        """Función interna para habilitar/deshabilitar un motor."""
        ena_line.set_value(1 if enable else 0)

    def move_forward(self, duration=1):
        """Mueve ambos motores hacia adelante."""
        print(f"Moviendo ambos motores hacia adelante por {duration} segundos...")
        # Motor Izquierdo adelante
        self._set_motor_direction(self.lines["left_forward"], self.lines["left_backward"], 1, 0)
        self._enable_motor(self.lines["left_ena"], True)
        # Motor Derecho adelante
        self._set_motor_direction(self.lines["right_forward"], self.lines["right_backward"], 1, 0)
        self._enable_motor(self.lines["right_enb"], True)
        sleep(duration)
        self.stop_all_motors()

    def move_backward(self, duration=1):
        """Mueve ambos motores hacia atrás."""
        print(f"Moviendo ambos motores hacia atrás por {duration} segundos...")
        # Motor Izquierdo atrás
        self._set_motor_direction(self.lines["left_forward"], self.lines["left_backward"], 0, 1)
        self._enable_motor(self.lines["left_ena"], True)
        # Motor Derecho atrás
        self._set_motor_direction(self.lines["right_forward"], self.lines["right_backward"], 0, 1)
        self._enable_motor(self.lines["right_enb"], True)
        sleep(duration)
        self.stop_all_motors()

    def turn_left(self, duration=0.5):
        """Gira el carro hacia la izquierda (motor izquierdo atrás, motor derecho adelante)."""
        print(f"Girando a la izquierda por {duration} segundos...")
        # Motor Izquierdo atrás
        self._set_motor_direction(self.lines["left_forward"], self.lines["left_backward"], 0, 1)
        self._enable_motor(self.lines["left_ena"], True)
        # Motor Derecho adelante
        self._set_motor_direction(self.lines["right_forward"], self.lines["right_backward"], 1, 0)
        self._enable_motor(self.lines["right_enb"], True)
        sleep(duration)
        self.stop_all_motors()

    def turn_right(self, duration=0.5):
        """Gira el carro hacia la derecha (motor izquierdo adelante, motor derecho atrás)."""
        print(f"Girando a la derecha por {duration} segundos...")
        # Motor Izquierdo adelante
        self._set_motor_direction(self.lines["left_forward"], self.lines["left_backward"], 1, 0)
        self._enable_motor(self.lines["left_ena"], True)
        # Motor Derecho atrás
        self._set_motor_direction(self.lines["right_forward"], self.lines["right_backward"], 0, 1)
        self._enable_motor(self.lines["right_enb"], True)
        sleep(duration)
        self.stop_all_motors()

    def stop_all_motors(self):
        """Detiene ambos motores."""
        print("Deteniendo todos los motores...")
        # Deshabilitar ambos ENA/ENB para cortar la energía
        self._enable_motor(self.lines["left_ena"], False)
        self._enable_motor(self.lines["right_enb"], False)
        # Asegurarse de que las direcciones estén en LOW
        self._set_motor_direction(self.lines["left_forward"], self.lines["left_backward"], 0, 0)
        self._set_motor_direction(self.lines["right_forward"], self.lines["right_backward"], 0, 0)

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
        # self.robot.close()
        # Liberar cada línea individualmente
        for name, line_obj in self.lines.items():
            if name != "chip": # No intentar liberar el objeto chip
                line_obj.release()
        self.lines["chip"].close() # Cerrar el chip GPIO al final

    def _continuous_move_worker(self):
        """
        Mantiene el robot moviéndose en la dirección indicada hasta que se cambie o se detenga.
        """
        while self._continuous_move_running:
            direction = self._continuous_direction
            speed = self._continuous_speed
            if direction == "forward":
                # self.robot.forward(speed)
                self.move_forward(0.2)
            elif direction == "backward":
                # self.robot.backward(speed)
                self.move_backward(0.2)
            elif direction == "left":
                # self.robot.left(speed)
                self.turn_left(0.2)
            elif direction == "right":
                # self.robot.right(speed)
                self.turn_right(0.2)
            elif direction == "stop" or direction is None:
                # self.robot.stop()
                self.stop_all_motors()
            # Repite cada 0.2 segundos para mantener el movimiento
            # sleep(0.2)

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
        # self.robot.stop()
        self.stop_all_motors()

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
                # self.robot.forward(speed)
                # sleep(duration)
                self.move_forward(duration)
            elif direction == "backward":
                # self.robot.backward(speed)
                # sleep(duration)
                self.move_backward(duration)
            elif direction == "left":
                # self.robot.left(speed)
                # sleep(duration)
                self.turn_left(duration)
            elif direction == "right":
                # self.robot.right(speed)
                # sleep(duration)
                self.turn_right(duration)
            else:
                # self.robot.stop()
                self.stop_all_motors()
