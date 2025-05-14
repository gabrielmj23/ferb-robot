import RPi.GPIO as GPIO
import time

# --- CONFIGURACIÓN DE PIN GPIO ---
# **MUY IMPORTANTE:** Reemplaza estos números con los pines GPIO BCM a los que
# realmente has conectado los pines INx y ENx del L298N.
# Usa `GPIO.setmode(GPIO.BCM)` si usas números BCM (recomendado).
# Usa `GPIO.setmode(GPIO.BOARD)` si usas la numeración física de los pines.

# Pines para el Motor Izquierdo (Motor A en muchos L298N)
MOTOR_LEFT_IN1 = 17 # Ejemplo: Conectado a GPIO 17 (BCM)
MOTOR_LEFT_IN2 = 18 # Ejemplo: Conectado a GPIO 18 (BCM)
ENABLE_LEFT = 27 # **DEBE** ser un pin capaz de PWM. Ejemplo: GPIO 27 (BCM)

# Pines para el Motor Derecho (Motor B en muchos L298N)
MOTOR_RIGHT_IN3 = 22 # Ejemplo: Conectado a GPIO 22 (BCM)
MOTOR_RIGHT_IN4 = 23 # Ejemplo: Conectado a GPIO 23 (BCM)
ENABLE_RIGHT = 24 # **DEBE** ser un pin capaz de PWM. Ejemplo: GPIO 24 (BCM)

# Frecuencia para el PWM (típicamente entre 50 y 100 Hz para motores DC)
PWM_FREQUENCY = 100

# Variables globales para los objetos PWM
pwm_left = None
pwm_right = None

# --- CONFIGURACIÓN INICIAL DE GPIO ---
def setup_gpio():
    """Configura el modo de pines, define los pines como salidas y configura PWM."""
    global pwm_left, pwm_right # Declara que usaremos las variables globales

    GPIO.setmode(GPIO.BCM) # Usar numeración BCM

    # Configurar pines de dirección como salidas
    GPIO.setup(MOTOR_LEFT_IN1, GPIO.OUT)
    GPIO.setup(MOTOR_LEFT_IN2, GPIO.OUT)
    GPIO.setup(MOTOR_RIGHT_IN3, GPIO.OUT)
    GPIO.setup(MOTOR_RIGHT_IN4, GPIO.OUT)

    # Configurar pines Enable como salidas
    GPIO.setup(ENABLE_LEFT, GPIO.OUT)
    GPIO.setup(ENABLE_RIGHT, GPIO.OUT)

    # Configurar objetos PWM
    pwm_left = GPIO.PWM(ENABLE_LEFT, PWM_FREQUENCY)
    pwm_right = GPIO.PWM(ENABLE_RIGHT, PWM_FREQUENCY)

    # Iniciar PWM con ciclo de trabajo 0 (motores parados)
    pwm_left.start(0)
    pwm_right.start(0)

    print("Configuración de GPIO y PWM completada.")

# --- FUNCIONES DE MOVIMIENTO CON VELOCIDAD ---

def set_speed(speed):
    """Ajusta la velocidad de ambos motores usando PWM."""
    # Asegura que la velocidad esté entre 0 y 100
    speed = max(0, min(100, speed))

    # Cambia el ciclo de trabajo (duty cycle) del PWM
    # Asegúrate de que los objetos PWM existen antes de usarlos
    if pwm_left and pwm_right:
        pwm_left.ChangeDutyCycle(speed)
        pwm_right.ChangeDutyCycle(speed)
    else:
        print("Error: Objetos PWM no inicializados.")


def stop():
    """Detiene ambos motores."""
    print("Deteniendo...")
    # Pone ambos pines de dirección de cada motor en LOW
    GPIO.output(MOTOR_LEFT_IN1, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW)

    # Pone el ciclo de trabajo PWM a 0
    set_speed(0)


def forward(speed=50):
    """Mueve el rover hacia adelante a una velocidad dada (0-100)."""
    print(f"Moviendo hacia adelante a velocidad {speed}...")
    # Motor Izquierdo (A) adelante
    GPIO.output(MOTOR_LEFT_IN1, GPIO.HIGH)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW)
    # Motor Derecho (B) adelante
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW)

    # Aplica la velocidad
    set_speed(speed)


def backward(speed=50):
    """Mueve el rover hacia atrás a una velocidad dada (0-100)."""
    print(f"Moviendo hacia atrás a velocidad {speed}...")
    # Motor Izquierdo (A) atrás
    GPIO.output(MOTOR_LEFT_IN1, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.HIGH)
    # Motor Derecho (B) atrás
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.HIGH)

    # Aplica la velocidad
    set_speed(speed)


def turn_left(speed=50):
    """Hace que el rover gire a la izquierda (giro sobre sí mismo) a una velocidad dada (0-100)."""
    # Para girar sobre sí mismo, una rueda va hacia adelante y la otra hacia atrás.
    # Por ejemplo, rueda izquierda atrás y rueda derecha adelante.
    print(f"Girando a la izquierda a velocidad {speed}...")
    # Motor Izquierdo (A) atrás
    GPIO.output(MOTOR_LEFT_IN1, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.HIGH)
    # Motor Derecho (B) adelante
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW)

    # Aplica la velocidad
    set_speed(speed)

    # Nota: Para giros más suaves (no sobre sí mismo), solo una rueda se mueve
    # y la otra podría estar parada o ir más lenta. Por ejemplo, solo mover rueda derecha:
    # GPIO.output(MOTOR_LEFT_IN1, GPIO.LOW)
    # GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW) # Izquierda parada
    # GPIO.output(MOTOR_RIGHT_IN3, GPIO.HIGH)
    # GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW) # Derecha adelante
    # pwm_left.ChangeDutyCycle(0) # Izquierda a 0 velocidad
    # pwm_right.ChangeDutyCycle(speed) # Derecha a velocidad


def turn_right(speed=50):
    """Hace que el rover gire a la derecha (giro sobre sí mismo) a una velocidad dada (0-100)."""
    # Para girar sobre sí mismo, una rueda va hacia adelante y la otra hacia atrás.
    # Por ejemplo, rueda izquierda adelante y rueda derecha atrás.
    print(f"Girando a la derecha a velocidad {speed}...")
    # Motor Izquierdo (A) adelante
    GPIO.output(MOTOR_LEFT_IN1, GPIO.HIGH)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW)
    # Motor Derecho (B) atrás
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.HIGH)

    # Aplica la velocidad
    set_speed(speed)

    # Nota: Para giros más suaves (no sobre sí mismo), solo una rueda se mueve
    # y la otra podría estar parada o ir más lenta. Por ejemplo, solo mover rueda izquierda:
    # GPIO.output(MOTOR_LEFT_IN1, GPIO.HIGH)
    # GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW) # Izquierda adelante
    # GPIO.output(MOTOR_RIGHT_IN3, GPIO.LOW)
    # GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW) # Derecha parada
    # pwm_left.ChangeDutyCycle(speed) # Izquierda a velocidad
    # pwm_right.ChangeDutyCycle(0) # Derecha a 0 velocidad


# --- BUCLE PRINCIPAL / EJEMPLO DE USO ---
if __name__ == "__main__":
    try:
        setup_gpio()

        print("Ejecutando secuencia de prueba con control de velocidad:")

        # Mover hacia adelante a media velocidad
        forward(speed=40)
        time.sleep(2)
        stop()
        time.sleep(1)

        # Mover hacia atrás a velocidad máxima
        backward(speed=100)
        time.sleep(2)
        stop()
        time.sleep(1)

        # Girar a la izquierda a velocidad moderada
        turn_left(speed=60)
        time.sleep(1.5)
        stop()
        time.sleep(1)

        # Girar a la derecha a baja velocidad
        turn_right(speed=30)
        time.sleep(1.5)
        stop()
        time.sleep(1)

        print("Secuencia de prueba terminada.")

    except KeyboardInterrupt:
        # Esto se ejecutará si presionas Ctrl+C para detener el script
        print("Interrumpido por el usuario.")

    finally:
        # Esto siempre se ejecutará al final
        stop() # Asegúrate de que los motores se detengan (esto pone PWM a 0)

        # Detiene los objetos PWM antes de limpiar GPIO
        # Asegúrate de que los objetos PWM existen antes de detenerlos
        if pwm_left:
            pwm_left.stop()
        if pwm_right:
            pwm_right.stop()

        GPIO.cleanup() # Limpia la configuración de GPIO
        print("Limpieza de GPIO completada.")