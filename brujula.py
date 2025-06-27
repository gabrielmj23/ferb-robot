import raspy_qmc5883l
import time


class Brujula:
    # UCAB_CALIBRATION = [
    #     [1.3166078114576967, -0.06412371173670786, -1874.4407833172772],
    #     [-0.06412371173670785, 1.0129872045416726, -3436.0563916932297],
    #     [0.0, 0.0, 1.0],
    # ]
    # UCAB_CALIBRATION = [
    #     [1.1514796082238565, -0.0784963968016999, 3065.490530172673],
    #     [-0.07849639680169994, 1.0406766586149614, -240.3239973414732],
    #     [0.0, 0.0, 1.0],
    # ]
    UCAB_CALIBRATION = [
        [1.1339814697578658, -0.08728362617636402, 2939.273917584574],
        [-0.08728362617636401, 1.0568618288205334, -429.28958308353225],
        [0.0, 0.0, 1.0],
    ]
    UCAB_DECLINATION = -15.9

    def __init__(self, i2c_bus=1, calibration=None, declination=None):
        """
        Initialize the compass sensor with the specified I2C bus, calibration, and declination.
        """
        self.sensor = raspy_qmc5883l.QMC5883L(i2c_bus=i2c_bus)
        if calibration is not None:
            self.sensor.calibration = calibration

        if declination is not None:
            self.sensor.declination = declination

    def run(self):
        """
        Continuously read and print the compass bearing.

        This is a test function
        """
        try:
            while True:
                bearing = self.sensor.get_bearing()
                if bearing:
                    print(f"Bearing: {bearing:.2f}°")
                time.sleep(0.25)
        except KeyboardInterrupt:
            print("Compass reading stopped.")
