import RPi.GPIO as GPIO
import time

# --- Configuración de Pines GPIO ---
# Usa el modo BOARD para referirte a los números de pin físicos en la Raspberry Pi.
# Puedes cambiar a GPIO.BCM si prefieres usar los números GPIO.
GPIO.setmode(GPIO.BOARD)

# Define los pines que conectaste a tu driver de motor (por ejemplo, L298N)
# Asegúrate de que estos pines coincidan con tu conexión real.
IN1 = 26  # Pin de entrada 1 del driver (controla la dirección)
IN2 = 21  # Pin de entrada 2 del driver (controla la dirección)
ENA = 18  # Pin de habilitación (Enable) del driver (controla la velocidad mediante PWM)

# Configura los pines como salidas
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)

# --- Configuración de PWM (Modulación por Ancho de Pulso) ---
# Crea un objeto PWM en el pin ENA con una frecuencia de 1000 Hz.
# Una frecuencia de 1000 Hz (1 kHz) es un buen punto de partida para motores DC.
pwm = GPIO.PWM(ENA, 1000)

# Inicia el PWM con un ciclo de trabajo (duty cycle) del 50%.
# El ciclo de trabajo controla la velocidad del motor (0% = detenido, 100% = velocidad máxima).
pwm.start(50)

# --- Funciones para controlar el motor ---
def forward(speed):
    """Gira el motor hacia adelante."""
    print(f"Girando hacia adelante a {speed}% de velocidad...")
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    pwm.ChangeDutyCycle(speed)

def backward(speed):
    """Gira el motor hacia atrás."""
    print(f"Girando hacia atrás a {speed}% de velocidad...")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    pwm.ChangeDutyCycle(speed)

def stop_motor():
    """Detiene el motor."""
    print("Deteniendo el motor...")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    pwm.ChangeDutyCycle(0) # Establece el ciclo de trabajo a 0 para asegurar el paro

# --- Secuencia de Prueba ---
try:
    print("Iniciando prueba de motor...")

    # Prueba hacia adelante a diferentes velocidades
    forward(30) # Baja velocidad
    time.sleep(2)
    forward(70) # Velocidad media
    time.sleep(2)
    forward(100) # Velocidad máxima
    time.sleep(2)

    # Prueba hacia atrás a diferentes velocidades
    backward(30)
    time.sleep(2)
    backward(70)
    time.sleep(2)
    backward(100)
    time.sleep(2)

    stop_motor() # Detiene el motor
    time.sleep(1) # Espera un segundo antes de finalizar

except KeyboardInterrupt:
    # Captura Ctrl+C para una salida limpia
    print("\nPrueba interrumpida por el usuario.")
    stop_motor() # Asegúrate de detener el motor al salir

finally:
    # Limpieza final de los pines GPIO
    print("Limpiando pines GPIO...")
    pwm.stop() # Detiene el PWM
    GPIO.cleanup() # Libera todos los pines GPIO
    print("Prueba de motor finalizada.")
