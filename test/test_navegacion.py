import time
import math
from gps import GPS
import raspy_qmc5883l
from gpiozero import Robot, Motor

# Configuración de robot y sensores
robot = Robot(left=Motor(26, 21, enable=18), right=Motor(0, 25, enable=27))
gps = GPS()
sensor = raspy_qmc5883l.QMC5883L(i2c_bus=4)
sensor.calibration = [
    [1.3166078114576967, -0.06412371173670786, -1874.4407833172772],
    [-0.06412371173670785, 1.0129872045416726, -3436.0563916932297],
    [0.0, 0.0, 1.0],
]
sensor.declination = -15.9


def get_current_position():
    while True:
        data = gps.read_data()
        if data and "Latitude" in data:
            try:
                lat = float(data.split(",")[0].split(":")[1])
                lon = float(data.split(",")[1].split(":")[1])
                return lat, lon
            except Exception:
                continue
        time.sleep(0.2)


def get_bearing_to_target(lat1, lon1, lat2, lon2):
    # Fórmula de rumbo entre dos puntos
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    diffLong = math.radians(lon2 - lon1)
    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (
        math.sin(lat1) * math.cos(lat2) * math.cos(diffLong)
    )
    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing


def get_current_heading():
    return sensor.get_bearing()


def turn_to_heading(target_heading, tolerance=5):
    while True:
        current_heading = get_current_heading()
        diff = (target_heading - current_heading + 360) % 360
        if diff < tolerance or diff > 360 - tolerance:
            robot.stop()
            break
        elif diff < 180:
            robot.right(speed=0.5)
        else:
            robot.left(speed=0.5)
        time.sleep(0.1)
    robot.stop()


def main():
    # Coordenadas objetivo (ejemplo)
    target_lat = float(input("Latitud objetivo: "))
    target_lon = float(input("Longitud objetivo: "))
    print("Obteniendo posición actual...")
    lat, lon = get_current_position()
    print(f"Posición actual: {lat}, {lon}")
    print("Calculando rumbo...")
    bearing = get_bearing_to_target(lat, lon, target_lat, target_lon)
    print(f"Rumbo objetivo: {bearing:.2f}°")
    print("Girando hacia el objetivo...")
    turn_to_heading(bearing)
    print("Avanzando 5 segundos...")
    robot.forward(speed=0.7)
    time.sleep(5)
    robot.stop()
    print("Listo.")


if __name__ == "__main__":
    main()
