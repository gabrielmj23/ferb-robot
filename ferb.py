from gpiozero import Robot, Motor
from time import sleep
import cv2


class Ferb:
    def __init__(
        self, left_motor_pins=(17, 18), right_motor_pins=(22, 23), initial_mode="manual"
    ):
        """
        Setup the robot with the given motor pins.
        """
        self.robot = Robot(left=Motor(*left_motor_pins), right=Motor(*right_motor_pins))
        self.current_mode = initial_mode
        self.camera = None

    def start_camera(self, camera_index=0):
        """
        Initialize the camera.
        """
        if self.camera is None:
            self.camera = cv2.VideoCapture(camera_index)

    def stop_camera(self):
        """
        Release the camera resource.
        """
        if self.camera is not None:
            self.camera.release()
            self.camera = None

    def camera_stream(self):
        """
        Generator that yields camera frames as JPEG for streaming.
        """
        self.start_camera()
        while True:
            if self.camera is None:
                break
            ret, frame = self.camera.read()
            if not ret:
                continue
            ret, jpeg = cv2.imencode(".jpg", frame)
            if not ret:
                continue
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
            )

    def cleanup(self):
        """
        Cleanup the robot resources.
        """
        self.stop_camera()
        self.robot.close()

    def move(self, direction: str, speed: float):
        """
        Handle movement.
        """
        if self.current_mode == "manual":
            speed = max(0, min(speed, 1))
            if direction == "forward":
                self.robot.forward(speed)  # type: ignore
                sleep(1)
            elif direction == "backward":
                self.robot.backward(speed)  # type: ignore
                sleep(1)
            elif direction == "left":
                self.robot.left(speed)  # type: ignore
                sleep(1)
            elif direction == "right":
                self.robot.right(speed)  # type: ignore
                sleep(1)
            else:
                self.robot.stop()
            # print("Moving robot:", direction, "at speed", speed)
        else:
            raise RuntimeError("El modo actual no permite el movimiento manual")
