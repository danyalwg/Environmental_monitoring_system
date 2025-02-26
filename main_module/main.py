#!/usr/bin/env python3
import json
from time import sleep
import time

# Import your sensor modules (adjust these imports as needed)
from mq import read_sensors
from uv import read_uv_sensor
from bme import read_bme280
from rtc import get_time
from dust_sensor import read_dust_sensor
import sd_card_logging  # SD card logging module

# Import your ESP‑NOW helper module (assumed already set up)
import lora

# Initialize the SD card and create a new CSV file on startup.
sd_card_logging.init_sd_card()
sd_card_logging.create_new_csv()

# Set the receiver’s MAC address (update this to your receiver’s MAC)
receiver_mac = b'\x14\x2b\x2f\xc4\xc7\x5c'
lora.add_peer(receiver_mac)

def main():
    while True:
        # ---------------------------
        # 1. Read Sensor Data
        # ---------------------------
        rtc = get_time()          # Expected keys: 'year', 'month', 'day', 'hour', 'minute', 'second'
        mq_data = read_sensors()    # Expected to return a dict for MQ‑9 and MQ‑135 sensors
        uv_data = read_uv_sensor()  # Expected keys: 'Raw_ADC', 'UV_Intensity', 'UV_Index'
        bme_data = read_bme280()    # Expected keys: 'Temperature', 'Pressure', 'Humidity'
        dust_data = read_dust_sensor()  # Expected keys: 'Raw_ADC', 'Dust_Density', 'AQI', 'Health_Level'

        # ---------------------------
        # 2. Create the Full Sensor Packet (for printing & logging)
        # ---------------------------
        rtc_date = f"{rtc['year']}/{rtc['month']:02}/{rtc['day']:02}"
        rtc_time = f"{rtc['hour']:02}:{rtc['minute']:02}:{rtc['second']:02}"
        sensor_packet = {
            "rtc": {
                "date": rtc_date,
                "time": rtc_time
            },
            "mq9": {
                "LPG": {"value": mq_data.get("MQ-9", {}).get("LPG", 0), "unit": "ppm"},
                "CO": {"value": mq_data.get("MQ-9", {}).get("CO", 0), "unit": "ppm"},
                "CH4": {"value": mq_data.get("MQ-9", {}).get("CH4", 0), "unit": "ppm"}
            },
            "mq135": {
                "CO2": {"value": mq_data.get("MQ-135", {}).get("CO2", 0), "unit": "ppm"},
                "CO": {"value": mq_data.get("MQ-135", {}).get("CO", 0), "unit": "ppm"},
                "alcohol": {"value": mq_data.get("MQ-135", {}).get("Ethanol", 0), "unit": "ppm"},
                "NH4": {"value": mq_data.get("MQ-135", {}).get("NH4", 0), "unit": "ppm"},
                "toluene": {"value": mq_data.get("MQ-135", {}).get("Toluene", 0), "unit": "ppm"},
                "acetone": {"value": mq_data.get("MQ-135", {}).get("Acetone", 0), "unit": "ppm"}
            },
            "uv_sensor": {
                "raw_adc": {"value": uv_data.get("Raw_ADC", 0), "unit": "counts"},
                "voltage": {"value": round(uv_data.get("Raw_ADC", 0) * 0.0008, 2), "unit": "V"},
                "uv_intensity": {"value": round(uv_data.get("UV_Intensity", 0), 2), "unit": "mW/cm²"},
                "uv_index": {"value": round(uv_data.get("UV_Index", 0), 2), "unit": "index"}
            },
            "bme280": {
                "temperature": {"value": round(bme_data.get("Temperature", 0), 2), "unit": "°C"},
                "pressure": {"value": round(bme_data.get("Pressure", 0), 2), "unit": "hPa"},
                "humidity": {"value": round(bme_data.get("Humidity", 0), 2), "unit": "%"}
            },
            "dust_sensor": {
                "raw_adc": {"value": dust_data.get("Raw_ADC", 0), "unit": "counts"},
                "voltage": {"value": round(dust_data.get("Raw_ADC", 0) * (1.0 / 820), 2), "unit": "V"},
                "dust_density": {"value": round(dust_data.get("Dust_Density", 0), 2), "unit": "µg/m³"},
                "AQI": {"value": dust_data.get("AQI", 0), "unit": "AQI"},
                "health_level": {"value": dust_data.get("Health_Level", ""), "unit": ""}
            }
        }

        # Print the full sensor packet (this is what your GUI sees)
        print(json.dumps(sensor_packet))
        # Log the sensor values to the SD card
        sd_card_logging.log_to_csv(sensor_packet)

        # ---------------------------
        # 3. Create the Sending Array (compact version)
        # ---------------------------
        send_array = [
            rtc_date,                                      # 0: RTC date (e.g., "2025/02/12")
            rtc_time,                                      # 1: RTC time (e.g., "09:55:29")
            mq_data.get("MQ-9", {}).get("LPG", 0),           # 2: MQ‑9 LPG
            mq_data.get("MQ-9", {}).get("CO", 0),            # 3: MQ‑9 CO
            mq_data.get("MQ-9", {}).get("CH4", 0),           # 4: MQ‑9 CH₄
            mq_data.get("MQ-135", {}).get("CO2", 0),         # 5: MQ‑135 CO₂
            mq_data.get("MQ-135", {}).get("CO", 0),          # 6: MQ‑135 CO
            mq_data.get("MQ-135", {}).get("Ethanol", 0),       # 7: MQ‑135 alcohol (Ethanol)
            mq_data.get("MQ-135", {}).get("NH4", 0),         # 8: MQ‑135 NH₄
            mq_data.get("MQ-135", {}).get("Toluene", 0),       # 9: MQ‑135 toluene
            mq_data.get("MQ-135", {}).get("Acetone", 0),       # 10: MQ‑135 acetone
            uv_data.get("Raw_ADC", 0),                        # 11: UV sensor raw_adc
            round(uv_data.get("Raw_ADC", 0) * 0.0008, 2),      # 12: UV sensor voltage
            round(uv_data.get("UV_Intensity", 0), 2),          # 13: UV sensor intensity
            round(uv_data.get("UV_Index", 0), 2),              # 14: UV sensor index
            round(bme_data.get("Temperature", 0), 2),          # 15: BME280 temperature
            round(bme_data.get("Pressure", 0), 2),             # 16: BME280 pressure
            round(bme_data.get("Humidity", 0), 2),             # 17: BME280 humidity
            dust_data.get("Raw_ADC", 0),                       # 18: Dust sensor raw_adc
            round(dust_data.get("Raw_ADC", 0) * (1.0 / 820), 2), # 19: Dust sensor voltage
            round(dust_data.get("Dust_Density", 0), 2),        # 20: Dust sensor dust_density
            dust_data.get("AQI", 0),                           # 21: Dust sensor AQI
            dust_data.get("Health_Level", "")                  # 22: Dust sensor health_level
        ]

        # Send the compact array via ESP‑NOW
        lora.send_packet(send_array, receiver_mac)

        sleep(1)

if __name__ == "__main__":
    main()
