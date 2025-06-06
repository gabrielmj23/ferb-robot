import raspy_qmc5883l
import time

"""
BRUJULA
VCC - PIN 1
GND - PIN 14
SDA - PIN 16 (GPIO 23)
SCL - PIN 18 (GPIO 24)
"""

sensor = raspy_qmc5883l.QMC5883L(i2c_bus=4)
m = sensor.get_magnet()
print(m)

# Calibrar
sensor.calibration = [
    [1.3166078114576967, -0.06412371173670786, -1874.4407833172772],
    [-0.06412371173670785, 1.0129872045416726, -3436.0563916932297],
    [0.0, 0.0, 1.0]
]
sensor.declination = -15.9


while True:
    print(sensor.get_bearing())
    time.sleep(0.5)
