from machine import ADC, Pin
from time import sleep

# Pin configuration for MQ-9 and MQ-135 sensors
mq9_analog = ADC(Pin(35))         # MQ-9 sensor connected to GPIO35
mq9_analog.atten(ADC.ATTN_11DB)     # Full-scale voltage: 3.3V
mq9_analog.width(ADC.WIDTH_12BIT)   # 12-bit resolution (0-4095)

mq135_analog = ADC(Pin(32))         # MQ-135 sensor connected to GPIO32
mq135_analog.atten(ADC.ATTN_11DB)
mq135_analog.width(ADC.WIDTH_12BIT)

# Calibration (baseline) resistance values measured in clean air
R0_MQ9 = 30.213
R0_MQ135 = 227.195

# Mapping functions for both sensors so that in clean air (ratio ~1) the value is 10 ppm.
def calculate_concentration_mq9(ratio, gas):
    if ratio >= 0.9:
        return 10
    elif ratio >= 0.7:
        return 20
    elif ratio >= 0.5:
        return 100
    else:
        return 200

def calculate_concentration_mq135(ratio, gas):
    if ratio >= 0.9:
        return 10
    elif ratio >= 0.7:
        return 20
    elif ratio >= 0.5:
        return 100
    else:
        return 200

def read_sensors():
    # --- MQ-9 sensor reading ---
    sensor_value_mq9 = mq9_analog.read()
    sensor_voltage_mq9 = (sensor_value_mq9 / 4095.0) * 3.3
    rs_mq9 = (3.3 - sensor_voltage_mq9) / sensor_voltage_mq9 if sensor_voltage_mq9 > 0 else 0
    ratio_mq9 = rs_mq9 / R0_MQ9 if rs_mq9 > 0 else 0

    # --- MQ-135 sensor reading ---
    sensor_value_mq135 = mq135_analog.read()
    sensor_voltage_mq135 = (sensor_value_mq135 / 4095.0) * 3.3
    # If sensor_voltage is zero (e.g., sensor not giving a reading), assume clean air (ratio = 1)
    if sensor_voltage_mq135 > 0:
        rs_mq135 = (3.3 - sensor_voltage_mq135) / sensor_voltage_mq135
        ratio_mq135 = rs_mq135 / R0_MQ135
    else:
        ratio_mq135 = 1.0

    # Calculate concentrations for MQ-9 gases
    concentration_lpg = calculate_concentration_mq9(ratio_mq9, "LPG")
    concentration_co_mq9 = calculate_concentration_mq9(ratio_mq9, "CO")
    concentration_ch4 = calculate_concentration_mq9(ratio_mq9, "CH4")

    # Calculate concentrations for MQ-135 gases
    concentration_co2 = calculate_concentration_mq135(ratio_mq135, "CO2")
    concentration_co_mq135 = calculate_concentration_mq135(ratio_mq135, "CO")
    concentration_nh3 = calculate_concentration_mq135(ratio_mq135, "NH4")
    concentration_ethanol = calculate_concentration_mq135(ratio_mq135, "Ethanol")
    concentration_toluene = calculate_concentration_mq135(ratio_mq135, "Toluene")
    concentration_acetone = calculate_concentration_mq135(ratio_mq135, "Acetone")

    return {
        "MQ-9": {
            "Raw_ADC": sensor_value_mq9,
            "Voltage": sensor_voltage_mq9,
            "Rs/R0": ratio_mq9,
            "LPG": concentration_lpg,
            "CO": concentration_co_mq9,
            "CH4": concentration_ch4
        },
        "MQ-135": {
            "Raw_ADC": sensor_value_mq135,
            "Voltage": sensor_voltage_mq135,
            "Rs/R0": ratio_mq135,
            "CO2": concentration_co2,
            "CO": concentration_co_mq135,
            "NH4": concentration_nh3,
            "Ethanol": concentration_ethanol,
            "Toluene": concentration_toluene,
            "Acetone": concentration_acetone
        }
    }

if __name__ == "__main__":
    while True:
        data = read_sensors()
        print("MQ-9 Data:", data["MQ-9"])
        print("MQ-135 Data:", data["MQ-135"])
        sleep(1)

