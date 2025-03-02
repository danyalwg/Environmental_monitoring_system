import time
from machine import ADC, Pin

# Setup for MQ-9 sensor on GPIO35
mq9_analog = ADC(Pin(35))
mq9_analog.atten(ADC.ATTN_11DB)    # Configure for full-scale 3.3V
mq9_analog.width(ADC.WIDTH_12BIT)  # 12-bit resolution (0-4095)

# Setup for MQ-135 sensor on GPIO32
mq135_analog = ADC(Pin(32))
mq135_analog.atten(ADC.ATTN_11DB)
mq135_analog.width(ADC.WIDTH_12BIT)

def read_rs(analog_sensor):
    """
    Reads the analog value, converts it to voltage,
    and calculates the sensor resistance Rs using the formula:
      Rs = (V_supply - V_sensor) / V_sensor
    where V_supply is assumed to be 3.3V.
    """
    adc_value = analog_sensor.read()
    voltage = (adc_value / 4095.0) * 3.3
    if voltage > 0:
        rs = (3.3 - voltage) / voltage
    else:
        rs = 0
    return rs

def main():
    duration = 60  # Duration to run in seconds (1 minute)
    start_time = time.time()
    sample_count = 0
    total_rs_mq9 = 0
    total_rs_mq135 = 0

    print("Starting baseline resistance measurement for 1 minute in clean air...")
    while time.time() - start_time < duration:
        rs_mq9 = read_rs(mq9_analog)
        rs_mq135 = read_rs(mq135_analog)
        total_rs_mq9 += rs_mq9
        total_rs_mq135 += rs_mq135
        sample_count += 1

        print("Sample {}: MQ-9 Rs = {:.3f}, MQ-135 Rs = {:.3f}".format(sample_count, rs_mq9, rs_mq135))
        time.sleep(1)  # Sample every 1 second

    # Calculate average (baseline) Rs values over the sampling period
    baseline_rs_mq9 = total_rs_mq9 / sample_count if sample_count else 0
    baseline_rs_mq135 = total_rs_mq135 / sample_count if sample_count else 0

    print("\nBaseline resistance values over {} seconds:".format(duration))
    print("MQ-9 Baseline Rs: {:.3f}".format(baseline_rs_mq9))
    print("MQ-135 Baseline Rs: {:.3f}".format(baseline_rs_mq135))

if __name__ == "__main__":
    main()

