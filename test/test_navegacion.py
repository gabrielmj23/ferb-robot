import time
import math
# from gps import GPS
import raspy_qmc5883l
from gpiozero import Robot, Motor
import serial
import pynmea2

class GPS:
    def __init__(self, port="/dev/ttyAMA0", baudrate=38400, timeout=0.5):
        """
        Initialize the GPS module with the specified serial port and settings.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.connect()
        
    def connect(self):
        """
        Connect to the GPS module.
        """
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print(f"Connected to GPS on {self.port} at {self.baudrate} baud.")
        except serial.SerialException as e:
            print(f"Failed to connect to GPS: {e}")

    def read_data(self):
        """
        Read data from the GPS module and parse it.
        """
        if not self.ser or not self.ser.is_open:
            print("GPS not connected.")
            return None

        try:
            newdata = self.ser.readline().decode('utf-8').strip()
            if newdata.startswith("$GNRMC"):
                print(f"GPS: {newdata}")
                newmsg = pynmea2.parse(newdata)
                lat = newmsg.latitude
                lng = newmsg.longitude
                if lat == 0.0 and lng == 0.0:
                    return "El GPS no se ha posicionado. Muévase a un sitio más despejado."
                gps_data = f"Latitude: {lat:.6f}, Longitude: {lng:.6f}"
                return gps_data
            else:
                return f"Received: {newdata}"
        except (pynmea2.ParseError, UnicodeDecodeError) as e:
            print(f"Error parsing GPS data: {e}")
            return None

    def close(self):
        """
        Close the GPS connection.
        """
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("GPS connection closed.")
    def run(self):
        """
        Continuously read and print GPS data.
        """
        try:
            while True:
                gps_data = self.read_data()
                if gps_data:
                    print(gps_data)
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("GPS reading stopped by user.")
        finally:
            self.close()


# Configuración de robot y sensores
robot = Robot(left=Motor(21, 26, enable=18), right=Motor(0, 25, enable=27))
gps = GPS()
sensor = raspy_qmc5883l.QMC5883L(i2c_bus=4)
# sensor.calibration = [
#     [1.3166078114576967, -0.06412371173670786, -1874.4407833172772],
#     [-0.06412371173670785, 1.0129872045416726, -3436.0563916932297],
#     [0.0, 0.0, 1.0],
# ]
# sensor.calibration = [
#     [1.1514796082238565, -0.0784963968016999, 3065.490530172673],
#     [-0.07849639680169994, 1.0406766586149614, -240.3239973414732],
#     [0.0, 0.0, 1.0],
# ]
sensor.calibration = [
    [1.1339814697578658, -0.08728362617636402, 2939.273917584574],
    [-0.08728362617636401, 1.0568618288205334, -429.28958308353225],
    [0.0, 0.0, 1.0],
]
sensor.declination = -15.9

# Latitud objetivo: 8.496388
# Longitud objetivo: -62.899166


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
            robot.right(speed=1)
        else:
            robot.left(speed=1)
        time.sleep(0.1)
    robot.stop()


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r


# def haversine(lat1, lon1, lat2, lon2):
#     # Calcula la distancia en metros entre dos coordenadas
#     R = 6371000  # Radio de la Tierra en metros
#     phi1 = math.radians(lat1)
#     phi2 = math.radians(lat2)
#     dphi = math.radians(lat2 - lat1)
#     dlambda = math.radians(lon2 - lon1)
#     a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(
#         dlambda / 2
#     ) ** 2
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
#     return R * c


def main():
    # Coordenadas objetivo (ejemplo)
    target_lat = float(input("Latitud objetivo: "))
    target_lon = float(input("Longitud objetivo: "))
    threshold = 2.0  # metros
    while True:
        print("Obteniendo posición actual...")
        lat, lon = get_current_position()
        dist = haversine(lat, lon, target_lat, target_lon)
        print(f"Posición actual: {lat}, {lon} (distancia al objetivo: {dist:.2f} m)")
        if dist < threshold:
            print("¡Objetivo alcanzado!")
            robot.stop()
            break
        print("Calculando rumbo...")
        bearing = get_bearing_to_target(lat, lon, target_lat, target_lon)
        print(f"Rumbo objetivo: {bearing:.2f}°")
        print("Girando hacia el objetivo...")
        turn_to_heading(bearing)
        print("Avanzando 10 segundos...")
        robot.forward(speed=1)
        time.sleep(10)
        robot.stop()
        print("Reevaluando posición...")
    print("Listo.")


if __name__ == "__main__":
    main()
