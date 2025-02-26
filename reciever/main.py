import network
import espnow
import json
import time

# --- Wi‑Fi & ESP‑NOW Initialization for Receiver ---
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

e = espnow.ESPNow()
e.active(True)

# --- Helper Function to Convert Compact Array to Full Packet ---
def convert_compact_to_full(compact):
    """
    Converts the compact array (list) into a full sensor packet dictionary.
    """
    # Extract values from compact array
    rtc_date         = compact[0]
    rtc_time         = compact[1]
    mq9_lpg          = compact[2]
    mq9_co           = compact[3]
    mq9_ch4          = compact[4]
    mq135_co2        = compact[5]
    mq135_co         = compact[6]
    mq135_alcohol    = compact[7]
    mq135_nh4        = compact[8]
    mq135_toluene    = compact[9]
    mq135_acetone    = compact[10]
    uv_raw_adc       = compact[11]
    uv_voltage       = compact[12]
    uv_intensity     = compact[13]
    uv_index         = compact[14]
    bme_temperature  = compact[15]
    bme_pressure     = compact[16]
    bme_humidity     = compact[17]
    dust_raw_adc     = compact[18]
    dust_voltage     = compact[19]
    dust_density     = compact[20]
    dust_aqi         = compact[21]
    dust_health      = compact[22]

    # Construct the full sensor packet dictionary
    full_packet = {
        "rtc": {
            "date": rtc_date,
            "time": rtc_time
        },
        "mq9": {
            "LPG": {"value": mq9_lpg, "unit": "ppm"},
            "CO": {"value": mq9_co, "unit": "ppm"},
            "CH4": {"value": mq9_ch4, "unit": "ppm"}
        },
        "mq135": {
            "CO2": {"value": mq135_co2, "unit": "ppm"},
            "CO": {"value": mq135_co, "unit": "ppm"},
            "alcohol": {"value": mq135_alcohol, "unit": "ppm"},
            "NH4": {"value": mq135_nh4, "unit": "ppm"},
            "toluene": {"value": mq135_toluene, "unit": "ppm"},
            "acetone": {"value": mq135_acetone, "unit": "ppm"}
        },
        "uv_sensor": {
            "raw_adc": {"value": uv_raw_adc, "unit": "counts"},
            "voltage": {"value": uv_voltage, "unit": "V"},
            "uv_intensity": {"value": uv_intensity, "unit": "mW/cm²"},
            "uv_index": {"value": uv_index, "unit": "index"}
        },
        "bme280": {
            "temperature": {"value": bme_temperature, "unit": "°C"},
            "pressure": {"value": bme_pressure, "unit": "hPa"},
            "humidity": {"value": bme_humidity, "unit": "%"}
        },
        "dust_sensor": {
            "raw_adc": {"value": dust_raw_adc, "unit": "counts"},
            "voltage": {"value": dust_voltage, "unit": "V"},
            "dust_density": {"value": dust_density, "unit": "µg/m³"},
            "AQI": {"value": dust_aqi, "unit": "AQI"},
            "health_level": {"value": dust_health, "unit": ""}
        }
    }
    return full_packet

# --- Receiver Loop ---
print("Receiver ready. Waiting for ESP‑NOW packets...")

while True:
    sender, msg = e.recv()  # Blocking call
    if msg:
        try:
            # Decode the received message (assumed to be a JSON-encoded compact array)
            data_str = msg.decode('utf-8')
            compact_packet = json.loads(data_str)
            # Convert the compact packet into the full sensor packet
            full_packet = convert_compact_to_full(compact_packet)
            # Print the full sensor packet as a JSON string (to USB serial)
            print(json.dumps(full_packet))
        except Exception as ex:
            print("Error processing received packet:", ex)
    time.sleep(0.1)
