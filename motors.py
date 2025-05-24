from gpiozero import Robot, Motor
import time

robot = Robot(
    left=Motor(17, 18),
    right=Motor(22, 23)
)

robot.forward(speed=1)
time.sleep(2)
robot.stop()
time.sleep(1)

robot.backward(speed=1)
time.sleep(2)
robot.stop()
time.sleep(1)

robot.left(speed=1)
time.sleep(1.5)
robot.stop()
time.sleep(1)

robot.right(speed=1)
time.sleep(1.5)
robot.stop()
time.sleep(1)
