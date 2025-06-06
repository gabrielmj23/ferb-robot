import serial
import time
import pynmea2

try:
    port = "/dev/ttyAMA0"
    baudrate = 38400
    timeout = 0.5
    ser = serial.Serial(port, baudrate, timeout=timeout)
    print(f"Conectado al puerto {port} con baudrate {baudrate}")

    while True:
        try:
            newdata = ser.readline().decode('utf-8').strip()
            if newdata:  # Imprimir cualquier línea que llegue
                print(f"Dato Recibido: {newdata}")
                if newdata.startswith("$GPRMC"):
                    try:
                        newmsg = pynmea2.parse(newdata)
                        lat = newmsg.latitude
                        lng = newmsg.longitude
                        gps = f"Latitud: {lat:.6f}, Longitud: {lng:.6f}"
                        print(gps)
                    except pynmea2.ParseError as e:
                        print(f"Error al parsear GPRMC: {e}")
        except serial.SerialException as e:
            print(f"Error de comunicación serial: {e}")
            break
        except UnicodeDecodeError as e:
            print(f"Error de decodificación: {e}")
        time.sleep(0.1)

except serial.SerialException as e:
    print(f"No se pudo abrir el puerto {port}: {e}")

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Puerto serial cerrado.")
