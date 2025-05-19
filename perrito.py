# main_robot_control.py
import cv2
import time

# Importar nuestros módulos personalizados
import vision_modulo
import motor_modulo

# --- Configuración de Control del Robot ---
# Estas dimensiones deben coincidir con las usadas en vision_module después del reescalado
# Obtenemos estas dimensiones del vision_module para asegurar consistencia.
# FRAME_WIDTH se usa para calcular FRAME_CENTER_X.
# FRAME_HEIGHT se usa para dibujar en el display.
FRAME_WIDTH = vision_module.RESIZED_FRAME_WIDTH # Usar la constante de vision_module
# FRAME_HEIGHT se obtendrá dinámicamente

FRAME_CENTER_X = FRAME_WIDTH // 2

# Tolerancias y radios objetivo para el control
CENTER_X_TOLERANCE = 25
TARGET_RADIUS_MIN = 45
TARGET_RADIUS_MAX = 65
RADIUS_ADJUST_TOLERANCE = 7

# --- Lógica de Control Principal ---
def controlar_robot_acciones(circle_info):
    """
    Decide qué acción tomar basado en la información de la pelota detectada.
    Llama a las funciones de motor_module.
    """
    if circle_info is None:
        # Esta condición es más para el bucle principal, pero por si acaso.
        # print("controlar_robot_acciones: No se detectó pelota.")
        # motor_module.parar_todos_los_motores() # El bucle principal ya lo hace
        return

    x_pelota = circle_info["x"]
    radius_pelota = circle_info["radius"]

    error_x = x_pelota - FRAME_CENTER_X
    accion_rotacion_realizada = False

    # 1. Ajustar la rotación para centrar la pelota en X
    if abs(error_x) > CENTER_X_TOLERANCE:
        if error_x > 0: # Pelota a la derecha del centro
            print(f"CONTROL: Pelota a la DERECHA (error {error_x}px). Robot girando IZQUIERDA.")
            motor_module.motor_girar_izquierda()
        else: # Pelota a la izquierda del centro
            print(f"CONTROL: Pelota a la IZQUIERDA (error {error_x}px). Robot girando DERECHA.")
            motor_module.motor_girar_derecha()
        accion_rotacion_realizada = True
    else:
        # print(f"CONTROL: Centrado en X OK (error {error_x}px).")
        motor_module.asegurar_parada_rotacion() # Asegura que no haya movimiento residual de rotación

    # 2. Ajustar la distancia basada en el radio de la pelota
    # Solo ajustar distancia si no se realizó una acción de rotación en este ciclo
    # para evitar movimientos combinados que pueden ser erráticos con "ráfagas".
    accion_distancia_realizada = False
    if not accion_rotacion_realizada:
        if radius_pelota < TARGET_RADIUS_MIN - RADIUS_ADJUST_TOLERANCE:
            print(f"CONTROL: Pelota PEQUEÑA (radio {radius_pelota}px). Acercándose.")
            motor_module.motor_acercarse()
            accion_distancia_realizada = True
        elif radius_pelota > TARGET_RADIUS_MAX + RADIUS_ADJUST_TOLERANCE:
            print(f"CONTROL: Pelota GRANDE (radio {radius_pelota}px). Alejándose.")
            motor_module.motor_alejarse()
            accion_distancia_realizada = True
        else:
            # print(f"CONTROL: Distancia OK (radio {radius_pelota}px).")
            motor_module.asegurar_parada_distancia() # Asegura que no haya mov. residual de distancia
    else:
        # Si se rotó, no ajustar distancia en este ciclo. Asegurar parada.
        motor_module.asegurar_parada_distancia()


    if not accion_rotacion_realizada and not accion_distancia_realizada:
        print(f"CONTROL: Robot en posición y distancia objetivo (Error X: {error_x}, Radio: {radius_pelota}).")
        # motor_module.parar_todos_los_motores() # Ya parado por las funciones anteriores y ACTION_DURATION


# --- Bucle Principal ---
if __name__ == "__main__":
    print("Iniciando el control principal del robot...")
    picam2_instance = vision_module.setup_camera()
    
    # Obtener dimensiones procesadas del frame
    _, FRAME_HEIGHT = vision_module.get_initial_frame_dimensions(picam2_instance)
    vision_module.processed_frame_height = FRAME_HEIGHT # Actualizar en vision_module

    print(f"Controlador principal usando dimensiones: {FRAME_WIDTH}x{FRAME_HEIGHT}")
    print(f"Centro del frame en X: {FRAME_CENTER_X}")
    print(f"Tolerancia de centrado: +/- {CENTER_X_TOLERANCE}px")
    print(f"Rango de radio objetivo: {TARGET_RADIUS_MIN}px - {TARGET_RADIUS_MAX}px")

    try:
        while True:
            frame_raw = picam2_instance.capture_array("main")
            if frame_raw is None:
                print("Error: No se pudo capturar frame de la cámara.")
                time.sleep(0.1) # Esperar un poco antes de reintentar
                continue
            
            # Procesar el frame para detectar la pelota
            display_frame, detected_ball_info = vision_module.procesar_frame_para_pelota(frame_raw.copy())

            # Controlar el robot basado en la información de la pelota
            if detected_ball_info:
                controlar_robot_acciones(detected_ball_info)
            else:
                # Si no hay pelota, parar todos los motores y quizás iniciar una búsqueda.
                print("CONTROL: No se detectó pelota válida. Parando motores.")
                motor_module.parar_todos_los_motores()

            # Mostrar el frame con guías visuales
            cv2.line(display_frame, (FRAME_CENTER_X, 0), (FRAME_CENTER_X, FRAME_HEIGHT), (255, 0, 0), 1)
            cv2.line(display_frame, (FRAME_CENTER_X - CENTER_X_TOLERANCE, 0), (FRAME_CENTER_X - CENTER_X_TOLERANCE, FRAME_HEIGHT), (0, 255, 255), 1)
            cv2.line(display_frame, (FRAME_CENTER_X + CENTER_X_TOLERANCE, 0), (FRAME_CENTER_X + CENTER_X_TOLERANCE, FRAME_HEIGHT), (0, 255, 255), 1)
            cv2.imshow("Robot Control View", display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("Tecla 'q' presionada. Saliendo del programa...")
                break
            
            # Pequeña pausa para no sobrecargar CPU y permitir que las acciones del motor se completen
            # si ACTION_DURATION es muy corto o cero. Con ACTION_DURATION > 0 y stop() en cada motor,
            # este sleep puede ser muy corto o incluso innecesario.
            # time.sleep(0.01) 

    except KeyboardInterrupt:
        print("Interrupción por teclado detectada. Saliendo...")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
    finally:
        print("Finalizando y liberando recursos...")
        if picam2_instance and picam2_instance.started:
            picam2_instance.stop()
            print("Cámara detenida.")
        motor_module.parar_todos_los_motores() # Asegurarse de que los motores estén parados
        cv2.destroyAllWindows()
        print("Programa terminado.")
