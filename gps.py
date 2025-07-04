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
        if not self.ser or not self.ser.is_open:
            print("GPS not connected.")
            return None

        try:
            newdata = self.ser.readline().decode('utf-8').strip()
            if newdata.startswith(("$GNRMC", "$GPRMC")): # BN220 can output GNRMC or GPRMC
                msg = pynmea2.parse(newdata)
                # Check for GPS fix indicator (e.g., A = valid, V = invalid)
                # For RMC, the status character is at position 2 of the parsed message.
                if hasattr(msg, 'status') and msg.status == 'A':
                    lat = msg.latitude
                    lng = msg.longitude
                    if lat != 0.0 or lng != 0.0: # Check if coordinates are truly zero
                        return {"lat": lat, "lon": lng}
                    else:
                        print("GPS: Coordenadas 0.0, 0.0 - Posiblemente sin fix válido.")
                        return None # Return None for no valid fix
                else:
                    # print(f"GPS: RMC sin fix válido: {newdata}") # For debugging
                    return None
            # else:
                # print(f"GPS: Ignorando mensaje: {newdata}") # For debugging other NMEA sentences
            return None # Return None if not a GNRMC or invalid
        except (pynmea2.ParseError, UnicodeDecodeError) as e:
            print(f"Error parsing GPS data: {e}")
            return None
        except serial.SerialTimeoutException:
            print("GPS: Timeout reading serial data.") # For debugging
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
