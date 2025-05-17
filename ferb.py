from gpiozero import Robot, Motor
from time import sleep


class Ferb:
    def __init__(
        self, left_motor_pins=(17, 18), right_motor_pins=(22, 23), initial_mode="manual"
    ):
        """
        Setup the robot with the given motor pins.
        """
        self.robot = Robot(left=Motor(*left_motor_pins), right=Motor(*right_motor_pins))
        self.current_mode = initial_mode

    def cleanup(self):
        """
        Cleanup the robot resources.
        """
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
        else:
            raise RuntimeError("El modo actual no permite el movimiento manual")
