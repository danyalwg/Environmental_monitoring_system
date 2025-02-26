import machine
import random
from bme280 import BME280

# Configure I2C pins for ESP32
i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21))

# Initialize the BME280/BMP280 sensor
bme = BME280(i2c=i2c)

def read_bme280():
    """
    Reads temperature, pressure, and generates a random humidity value.

    Returns:
        dict: A dictionary with temperature (°C), pressure (hPa), and random humidity (%).
    """
    # Read sensor values
    values = bme.values  # Read as human-readable strings (e.g., '25.6C', '1013.2hPa')

    # Parse and convert values to numbers
    temperature = float(values[0][:-1])  # Remove 'C'
    pressure = float(values[1][:-3])     # Remove 'hPa'

    # Generate a random humidity value
    humidity = random.uniform(23, 26)  # Random value between 23% and 26%

    return {
        "Temperature": temperature,
        "Pressure": pressure,
        "Humidity": humidity  # Keep as a float
    }
