import gpiod
import time

# --- Configuración de Pines GPIO (BCM Offsets para gpiod) ---
# Asegúrate de que estos números de pin BCM coincidan con tu cableado real.

# Chip GPIO principal (casi siempre 'gpiochip0' en Raspberry Pi)
CHIP_NAME = "gpiochip0"

# Pines para el Motor Izquierdo
MOTOR_LEFT_FORWARD_PIN = 26    # GPIO 17 -> L298N IN1
MOTOR_LEFT_BACKWARD_PIN = 21   # GPIO 18 -> L298N IN2
MOTOR_LEFT_ENA_PIN = 18        # GPIO 12 -> L298N ENA (Enable Motor A)

# Pines para el Motor Derecho
MOTOR_RIGHT_FORWARD_PIN = 0   # GPIO 27 -> L298N IN3
MOTOR_RIGHT_BACKWARD_PIN = 25  # GPIO 22 -> L298N IN4
MOTOR_RIGHT_ENB_PIN = 27       # GPIO 13 -> L298N ENB (Enable Motor B)


# --- Inicialización de gpiod y Obtención de Líneas ---
def setup_motor_pins():
    """
    Configura los pines GPIO para los motores usando gpiod.
    Devuelve un diccionario de objetos gpiod.Line.
    """
    try:
        chip = gpiod.Chip(CHIP_NAME)
    except FileNotFoundError:
        print(f"Error: El chip GPIO '{CHIP_NAME}' no se encontró.")
        print("Asegúrate de que el módulo 'gpiod' está instalado y que estás en una Raspberry Pi.")
        exit()

    # Obtener las líneas individualmente para mejor control y legibilidad
    # Usamos gpiod.LINE_REQ_DIR_OUT como se corrigió anteriormente
    lines = {
        "left_forward": chip.get_line(MOTOR_LEFT_FORWARD_PIN),
        "left_backward": chip.get_line(MOTOR_LEFT_BACKWARD_PIN),
        "left_ena": chip.get_line(MOTOR_LEFT_ENA_PIN),
        "right_forward": chip.get_line(MOTOR_RIGHT_FORWARD_PIN),
        "right_backward": chip.get_line(MOTOR_RIGHT_BACKWARD_PIN),
        "right_enb": chip.get_line(MOTOR_RIGHT_ENB_PIN),
        "chip": chip # Guardamos el chip para poder cerrarlo en finally
    }

    # Solicitar las líneas como salidas
    for name, line_obj in lines.items():
        if name != "chip": # No solicitar el chip mismo
            line_obj.request(consumer=f"motor_{name}", type=gpiod.LINE_REQ_DIR_OUT)
            # Asegurarse de que estén apagadas al inicio
            line_obj.set_value(0)
    
    return lines

# --- Funciones de Control de Motores ---

def _set_motor_direction(forward_line, backward_line, forward_state, backward_state):
    """Función interna para establecer la dirección de un motor."""
    forward_line.set_value(forward_state)
    backward_line.set_value(backward_state)

def _enable_motor(ena_line, enable=True):
    """Función interna para habilitar/deshabilitar un motor."""
    ena_line.set_value(1 if enable else 0)

def move_forward(lines, duration=1):
    """Mueve ambos motores hacia adelante."""
    print(f"Moviendo ambos motores hacia adelante por {duration} segundos...")
    # Motor Izquierdo adelante
    _set_motor_direction(lines["left_forward"], lines["left_backward"], 1, 0)
    _enable_motor(lines["left_ena"], True)
    # Motor Derecho adelante
    _set_motor_direction(lines["right_forward"], lines["right_backward"], 1, 0)
    _enable_motor(lines["right_enb"], True)
    time.sleep(duration)
    stop_all_motors(lines) # Detener después de la duración

def move_backward(lines, duration=1):
    """Mueve ambos motores hacia atrás."""
    print(f"Moviendo ambos motores hacia atrás por {duration} segundos...")
    # Motor Izquierdo atrás
    _set_motor_direction(lines["left_forward"], lines["left_backward"], 0, 1)
    _enable_motor(lines["left_ena"], True)
    # Motor Derecho atrás
    _set_motor_direction(lines["right_forward"], lines["right_backward"], 0, 1)
    _enable_motor(lines["right_enb"], True)
    time.sleep(duration)
    stop_all_motors(lines) # Detener después de la duración

def turn_left(lines, duration=0.5):
    """Gira el carro hacia la izquierda (motor izquierdo atrás, motor derecho adelante)."""
    print(f"Girando a la izquierda por {duration} segundos...")
    # Motor Izquierdo atrás
    _set_motor_direction(lines["left_forward"], lines["left_backward"], 0, 1)
    _enable_motor(lines["left_ena"], True)
    # Motor Derecho adelante
    _set_motor_direction(lines["right_forward"], lines["right_backward"], 1, 0)
    _enable_motor(lines["right_enb"], True)
    time.sleep(duration)
    stop_all_motors(lines) # Detener después de la duración

def turn_right(lines, duration=0.5):
    """Gira el carro hacia la derecha (motor izquierdo adelante, motor derecho atrás)."""
    print(f"Girando a la derecha por {duration} segundos...")
    # Motor Izquierdo adelante
    _set_motor_direction(lines["left_forward"], lines["left_backward"], 1, 0)
    _enable_motor(lines["left_ena"], True)
    # Motor Derecho atrás
    _set_motor_direction(lines["right_forward"], lines["right_backward"], 0, 1)
    _enable_motor(lines["right_enb"], True)
    time.sleep(duration)
    stop_all_motors(lines) # Detener después de la duración

def stop_all_motors(lines):
    """Detiene ambos motores."""
    print("Deteniendo todos los motores...")
    # Deshabilitar ambos ENA/ENB para cortar la energía
    _enable_motor(lines["left_ena"], False)
    _enable_motor(lines["right_enb"], False)
    # Asegurarse de que las direcciones estén en LOW
    _set_motor_direction(lines["left_forward"], lines["left_backward"], 0, 0)
    _set_motor_direction(lines["right_forward"], lines["right_backward"], 0, 0)

# --- Bloque Principal de Ejecución ---
if __name__ == "__main__":
    # Configurar los pines GPIO
    # Capturamos el diccionario de líneas
    gpio_lines = setup_motor_pins()
    try:
        print("Iniciando secuencia de prueba de movimientos...")

        # Ejemplo de movimientos
        move_forward(gpio_lines, 1.5) # Mueve hacia adelante por 1.5 segundos
        time.sleep(1) # Pequeña pausa

        move_backward(gpio_lines, 1.5) # Mueve hacia atrás por 1.5 segundos
        time.sleep(1) # Pequeña pausa

        turn_left(gpio_lines, 1.5) # Gira a la izquierda por 1.5 segundos
        time.sleep(1) # Pequeña pausa

        turn_right(gpio_lines, 1.5) # Gira a la derecha por 1.5 segundos
        time.sleep(1) # Pequeña pausa

        print("Secuencia de prueba completada.")

    except KeyboardInterrupt:
        print("\nPrueba interrumpida por el usuario. Deteniendo motores...")
    finally:
        # Siempre asegurar que los motores se detengan y los pines se liberen
        stop_all_motors(gpio_lines)
        print("Liberando líneas GPIO...")
        # Liberar cada línea individualmente
        for name, line_obj in gpio_lines.items():
            if name != "chip": # No intentar liberar el objeto chip
                line_obj.release()
        gpio_lines["chip"].close() # Cerrar el chip GPIO al final
        print("Recursos GPIO liberados. ¡Hasta luego!")
