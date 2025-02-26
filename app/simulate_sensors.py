#!/usr/bin/env python3
import json
import time
import random
from datetime import datetime

def simulate_rtc():
    now = datetime.now()
    return {
        "date": now.strftime("%Y/%m/%d"),
        "time": now.strftime("%H:%M:%S")
    }

def simulate_mq9():
    return {
        "LPG": {"value": random.randint(0, 100), "unit": "ppm"},
        "CO": {"value": random.randint(0, 100), "unit": "ppm"},
        "CH4": {"value": random.randint(0, 100), "unit": "ppm"}
    }

def simulate_mq135():
    return {
        "CO2": {"value": random.randint(350, 450), "unit": "ppm"},
        "CO": {"value": random.randint(0, 10), "unit": "ppm"},
        "alcohol": {"value": random.randint(0, 50), "unit": "ppm"},
        "NH4": {"value": random.randint(0, 10), "unit": "ppm"},
        "toluene": {"value": random.randint(0, 50), "unit": "ppm"},
        "acetone": {"value": random.randint(0, 50), "unit": "ppm"}
    }

def simulate_uv_sensor():
    raw_adc = random.randint(500, 600)
    voltage = round(raw_adc * 0.0008, 2)  # conversion factor for simulation
    uv_intensity = round(random.uniform(0.4, 0.7), 2)  # in mW/cm²
    uv_index = round(random.uniform(4.5, 7.0), 2)
    return {
        "raw_adc": {"value": raw_adc, "unit": "counts"},
        "voltage": {"value": voltage, "unit": "V"},
        "uv_intensity": {"value": uv_intensity, "unit": "mW/cm²"},
        "uv_index": {"value": uv_index, "unit": "index"}
    }

def simulate_bme280():
    temperature = round(random.uniform(16.0, 20.0), 1)  # in °C
    pressure = round(random.uniform(1015.0, 1020.0), 1)   # in hPa
    humidity = round(random.uniform(35.0, 40.0), 1)       # in %
    return {
        "temperature": {"value": temperature, "unit": "°C"},
        "pressure": {"value": pressure, "unit": "hPa"},
        "humidity": {"value": humidity, "unit": "%"}
    }

def simulate_dust_sensor():
    raw_adc = random.randint(800, 900)
    voltage = round(raw_adc * (1.0 / 820), 2)  # simple conversion for simulation
    dust_density = round(random.uniform(45.0, 60.0), 2)  # in µg/m³
    aqi = random.randint(100, 150)
    if aqi <= 50:
        health_level = "Good"
    elif aqi <= 100:
        health_level = "Moderate"
    elif aqi <= 150:
        health_level = "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        health_level = "Unhealthy"
    else:
        health_level = "Very Unhealthy"
    return {
        "raw_adc": {"value": raw_adc, "unit": "counts"},
        "voltage": {"value": voltage, "unit": "V"},
        "dust_density": {"value": dust_density, "unit": "µg/m³"},
        "AQI": {"value": aqi, "unit": "AQI"},
        "health_level": {"value": health_level, "unit": ""}
    }

def simulate_sensor_packet():
    packet = {
        "rtc": simulate_rtc(),
        "mq9": simulate_mq9(),
        "mq135": simulate_mq135(),
        "uv_sensor": simulate_uv_sensor(),
        "bme280": simulate_bme280(),
        "dust_sensor": simulate_dust_sensor()
    }
    return packet

def run_simulation():
    """Continuously simulates sensor data packets and prints them as JSON."""
    try:
        while True:
            sensor_packet = simulate_sensor_packet()
            print(json.dumps(sensor_packet, indent=2))
            time.sleep(1)  # simulate a new packet every second
    except KeyboardInterrupt:
        print("\nSimulation stopped.")

# When imported, you can call simulate_sensor_packet() or run_simulation()
if __name__ == "__main__":
    run_simulation()
