from machine import ADC, Pin

# Pin configuration
uv_analog = ADC(Pin(33))          # UV sensor analog pin connected to GPIO33
uv_analog.atten(ADC.ATTN_11DB)    # Configure ADC for full-scale 3.3V
uv_analog.width(ADC.WIDTH_12BIT)  # 12-bit resolution (0-4095)

# Function to map a value (like Arduino's map for floats)
def map_float(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# Function to read and calculate UV intensity and index
def read_uv_sensor():
    # Average multiple readings for stability
    number_of_readings = 8
    running_value = 0
    for _ in range(number_of_readings):
        running_value += uv_analog.read()
    uv_level = running_value / number_of_readings

    # Calculate the sensor output voltage assuming a 3.3V reference
    output_voltage = uv_level * (3.3 / 4095.0)

    # Convert the voltage to UV intensity level (mW/cm^2)
    uv_intensity = map_float(output_voltage, 0.99, 2.8, 0.0, 15.0)
    if uv_intensity < 0:
        uv_intensity = 0

    # Convert UV intensity to UV Index
    uv_index = uv_intensity / 0.1  # Rough approximation

    # Return results as a dictionary
    return {
        "Raw_ADC": uv_level,
        "Voltage": output_voltage,
        "UV_Intensity": uv_intensity,
        "UV_Index": uv_index
    }
