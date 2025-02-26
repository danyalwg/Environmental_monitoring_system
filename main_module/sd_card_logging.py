import machine
import os
import time
import sdcard

# Global variables and constants
SD_MOUNT_POINT = "/sd"
csv_filename = None
sd_initialized = False

def init_sd_card(baudrate=1000000):
    """
    Initializes the SD card (if not already done) and mounts it.
    """
    global sd_initialized, sd
    if not sd_initialized:
        spi = machine.SPI(2,
                          baudrate=baudrate,
                          polarity=0,
                          phase=0,
                          sck=machine.Pin(18),
                          mosi=machine.Pin(23),
                          miso=machine.Pin(19))
        cs = machine.Pin(5, machine.Pin.OUT)
        sd = sdcard.SDCard(spi, cs)
        os.mount(sd, SD_MOUNT_POINT)
        sd_initialized = True

def create_new_csv():
    """
    Creates a new CSV file on the SD card. The file is named using the current date and time:
    logs_YYYYMMDD_HHMMSS.csv.
    A header row is written to the file.
    """
    global csv_filename
    t = time.localtime()  # Assumes RTC is already set correctly
    date_str = "{:04}{:02}{:02}".format(t[0], t[1], t[2])
    time_str = "{:02}{:02}{:02}".format(t[3], t[4], t[5])
    csv_filename = "logs_{}_{}.csv".format(date_str, time_str)
    full_path = SD_MOUNT_POINT + "/" + csv_filename
    with open(full_path, "w") as f:
        header = ("date,time,"
                  "MQ9_LPG,MQ9_CO,MQ9_CH4,"
                  "MQ135_CO2,MQ135_CO,MQ135_alcohol,MQ135_NH4,MQ135_toluene,MQ135_acetone,"
                  "UV_raw_adc,UV_voltage,UV_uv_intensity,UV_uv_index,"
                  "BME280_temperature,BME280_pressure,BME280_humidity,"
                  "Dust_raw_adc,Dust_voltage,Dust_dust_density,Dust_AQI,Dust_health_level\n")
        f.write(header)
    return full_path

def log_to_csv(sensor_packet):
    """
    Appends a row to the CSV file on the SD card.
    The sensor_packet is expected to be a dictionary with the structure produced in your main.py.
    """
    # Extract timestamp from the RTC data
    rtc = sensor_packet.get("rtc", {})
    date_str = rtc.get("date", "")
    time_str = rtc.get("time", "")
    
    # Extract MQ-9 sensor values
    mq9 = sensor_packet.get("mq9", {})
    mq9_LPG = mq9.get("LPG", {}).get("value", 0)
    mq9_CO = mq9.get("CO", {}).get("value", 0)
    mq9_CH4 = mq9.get("CH4", {}).get("value", 0)
    
    # Extract MQ-135 sensor values
    mq135 = sensor_packet.get("mq135", {})
    mq135_CO2 = mq135.get("CO2", {}).get("value", 0)
    mq135_CO = mq135.get("CO", {}).get("value", 0)
    mq135_alcohol = mq135.get("alcohol", {}).get("value", 0)
    mq135_NH4 = mq135.get("NH4", {}).get("value", 0)
    mq135_toluene = mq135.get("toluene", {}).get("value", 0)
    mq135_acetone = mq135.get("acetone", {}).get("value", 0)
    
    # Extract UV sensor values
    uv = sensor_packet.get("uv_sensor", {})
    uv_raw_adc = uv.get("raw_adc", {}).get("value", 0)
    uv_voltage = uv.get("voltage", {}).get("value", 0)
    uv_uv_intensity = uv.get("uv_intensity", {}).get("value", 0)
    uv_uv_index = uv.get("uv_index", {}).get("value", 0)
    
    # Extract BME280 sensor values
    bme = sensor_packet.get("bme280", {})
    bme_temperature = bme.get("temperature", {}).get("value", 0)
    bme_pressure = bme.get("pressure", {}).get("value", 0)
    bme_humidity = bme.get("humidity", {}).get("value", 0)
    
    # Extract Dust sensor values
    dust = sensor_packet.get("dust_sensor", {})
    dust_raw_adc = dust.get("raw_adc", {}).get("value", 0)
    dust_voltage = dust.get("voltage", {}).get("value", 0)
    dust_density = dust.get("dust_density", {}).get("value", 0)
    dust_AQI = dust.get("AQI", {}).get("value", 0)
    dust_health_level = dust.get("health_level", {}).get("value", "")
    
    # Create a CSV row string
    row = "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
        date_str, time_str,
        mq9_LPG, mq9_CO, mq9_CH4,
        mq135_CO2, mq135_CO, mq135_alcohol, mq135_NH4, mq135_toluene, mq135_acetone,
        uv_raw_adc, uv_voltage, uv_uv_intensity, uv_uv_index,
        bme_temperature, bme_pressure, bme_humidity,
        dust_raw_adc, dust_voltage, dust_density, dust_AQI, dust_health_level
    )
    full_path = SD_MOUNT_POINT + "/" + csv_filename
    with open(full_path, "a") as f:
        f.write(row)
