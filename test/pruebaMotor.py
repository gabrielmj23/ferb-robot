import gpiod
import time

# Configuración de los pines GPIO para los motores
CHIP_NAME = "gpiochip0"  # Nombre del chip GPIO (puede variar según tu configuración)
MOTOR_LEFT_FORWARD = 26  # GPIO para avanzar motor izquierdo
MOTOR_LEFT_BACKWARD = 21  # GPIO para retroceder motor izquierdo
MOTOR_RIGHT_FORWARD = 0  # GPIO para avanzar motor derecho
MOTOR_RIGHT_BACKWARD = 25  # GPIO para retroceder motor derecho

def setup_motor_pins():
    """Configura los pines GPIO para los motores."""
    chip = gpiod.Chip(CHIP_NAME)
    lines = chip.get_lines([MOTOR_LEFT_FORWARD, MOTOR_LEFT_BACKWARD, MOTOR_RIGHT_FORWARD, MOTOR_RIGHT_BACKWARD])
    lines.request(consumer="motor_control", type=gpiod.LINE_REQ_DIR_OUT)
    return lines

def control_motors(lines, left_motor, right_motor, duration):
    """
    Controla los motores del carro.

    :param lines: Líneas GPIO configuradas.
    :param left_motor: Tupla (forward, backward) para el motor izquierdo.
    :param right_motor: Tupla (forward, backward) para el motor derecho.
    :param duration: Duración en segundos para ejecutar el movimiento.
    """
    # Configurar los valores de los pines
    lines.set_values([left_motor[0], left_motor[1], right_motor[0], right_motor[1]])
    time.sleep(duration)
    # Detener los motores
    lines.set_values([0, 0, 0, 0])

def control_motors_pwm(lines, left_motor, right_motor, duration, duty_cycle=0.8, frequency=100):
    """
    Controla los motores usando PWM por software para mayor velocidad.
    :param duty_cycle: Proporción de tiempo encendido (0.0 a 1.0).
    :param frequency: Frecuencia del ciclo PWM en Hz.
    """
    period = 1.0 / frequency
    on_time = period * duty_cycle
    off_time = period * (1 - duty_cycle)
    end_time = time.time() + duration
    while time.time() < end_time:
        lines.set_values([left_motor[0], left_motor[1], right_motor[0], right_motor[1]])
        time.sleep(on_time)
        lines.set_values([0, 0, 0, 0])
        time.sleep(off_time)

def move_forward(lines, duration=1, fast=False):
    """Mueve el carro hacia adelante."""
    if fast:
        # Usa PWM por software para mayor velocidad
        control_motors_pwm(lines, (1, 0), (1, 0), duration, duty_cycle=1.0, frequency=200)
    else:
        control_motors(lines, (1, 0), (1, 0), duration)

def move_backward(lines, duration=1):
    """Mueve el carro hacia atrás."""
    control_motors(lines, (0, 1), (0, 1), duration)

def turn_left(lines, duration=0.5):
    """Gira el carro hacia la izquierda."""
    control_motors(lines, (0, 0), (1, 0), duration)

def turn_right(lines, duration=0.5):
    """Gira el carro hacia la derecha."""
    control_motors(lines, (1, 0), (0, 0), duration)

if __name__ == "__main__":
    # Configurar los pines GPIO
    lines = setup_motor_pins()
    try:
        # Ejemplo de movimientos con mayor duración
        #move_forward(lines, 15)
        move_forward(lines, 15, fast=True)  # Mueve hacia adelante a máxima velocidad por 15 segundos
        turn_left(lines, 15)
        #move_backward(lines, 15)
        turn_right(lines, 15)
    finally:
        # Liberar los pines GPIO al finalizar
        lines.release()
