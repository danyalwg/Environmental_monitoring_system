from machine import ADC, Pin
from time import sleep_us, sleep

# Pin definitions
measure_pin = ADC(Pin(34))  # Analog pin for dust sensor
led_power = Pin(4, Pin.OUT)  # LED driver pin

# ADC configuration
measure_pin.atten(ADC.ATTN_11DB)    # Configure for 3.3V input range
measure_pin.width(ADC.WIDTH_12BIT)  # 12-bit resolution (0-4095)

# Timing parameters
sampling_time = 280  # Microseconds
delta_time = 40      # Microseconds
sleep_time = 9680    # Microseconds

def calculate_aqi(dust_density):
    """
    Calculate the Air Quality Index (AQI) based on the dust density (µg/m³).
    """
    if dust_density <= 12:
        return int((dust_density / 12) * 50)  # Good
    elif dust_density <= 35.4:
        return int(((dust_density - 12.1) / (35.4 - 12.1)) * (100 - 51) + 51)  # Moderate
    elif dust_density <= 55.4:
        return int(((dust_density - 35.5) / (55.4 - 35.5)) * (150 - 101) + 101)  # Unhealthy for Sensitive Groups
    elif dust_density <= 150.4:
        return int(((dust_density - 55.5) / (150.4 - 55.5)) * (200 - 151) + 151)  # Unhealthy
    elif dust_density <= 250.4:
        return int(((dust_density - 150.5) / (250.4 - 150.5)) * (300 - 201) + 201)  # Very Unhealthy
    elif dust_density <= 500.4:
        return int(((dust_density - 250.5) / (500.4 - 250.5)) * (500 - 301) + 301)  # Hazardous
    else:
        return 500  # Beyond AQI scale

def get_health_level(aqi):
    """
    Get the health level description based on AQI.
    """
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    elif aqi <= 500:
        return "Hazardous"
    else:
        return "Beyond AQI Scale"

def read_dust_sensor():
    """
    Reads the GP2Y1014AU0F dust sensor and calculates dust density, AQI, and health level.

    Returns:
        dict: Contains raw ADC, voltage, dust density, AQI, and health level.
    """
    # Power on the LED
    led_power.value(0)
    sleep_us(sampling_time)

    # Read analog value
    vo_measured = measure_pin.read()

    # Turn off the LED
    sleep_us(delta_time)
    led_power.value(1)

    # Wait before next measurement
    sleep_us(sleep_time)

    # Convert ADC value to voltage
    calc_voltage = (vo_measured / 4095.0) * 5.0  # Adjusted for 5V logic

    # Calculate dust density using the equation from Chris Nafis
    dust_density = max(170 * calc_voltage - 0.1, 0)  # Avoid negative values

    # Calculate AQI
    aqi = calculate_aqi(dust_density)

    # Determine health level
    health_level = get_health_level(aqi)

    return {
        "Raw_ADC": vo_measured,
        "Voltage": calc_voltage,
        "Dust_Density": dust_density,  # µg/m³
        "AQI": aqi,
        "Health_Level": health_level
    }
