import serial
import time
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
            while True:
                newdata = self.ser.readline().decode('utf-8').strip()
                if newdata.startswith("$GNRMC"):
                    newmsg = pynmea2.parse(newdata)
                    lat = newmsg.latitude
                    lng = newmsg.longitude
                    if lat == 0.0 and lng == 0.0:
                        return "El GPS no se ha posicionado. Muévase a un sitio más despejado."
                    gps_data = f"Latitude: {lat:.6f}, Longitude: {lng:.6f}"
                    return {"lat": lat, "lon": lng}
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
