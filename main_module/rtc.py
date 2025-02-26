from ds3231 import DS3231
from machine import I2C, Pin

# Configure I2C pins for ESP32
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
rtc = DS3231(i2c)

def get_time():
    """
    Reads the current time from the DS3231 RTC correctly.

    Returns:
        dict: A dictionary with keys 'year', 'month', 'day', 'hour', 'minute', 'second', and 'weekday'.
    """
    datetime = rtc.datetime()
    
    return {
        "year": datetime[0],   # Year
        "month": datetime[1],  # Month
        "day": datetime[2],    # Day
        "hour": datetime[4],   # Corrected index for Hour
        "minute": datetime[5], # Corrected index for Minute
        "second": datetime[6], # Corrected index for Second
        "weekday": datetime[3] # 1=Monday, 7=Sunday
    }


def set_time(year, month, day, hour, minute, second):
    """
    Sets the current time on the DS3231 RTC.

    Args:
        year (int): The year (2000-2099).
        month (int): The month (1-12).
        day (int): The day of the month (1-31).
        hour (int): The hour (0-23).
        minute (int): The minute (0-59).
        second (int): The second (0-59).
    """
    datetime = (year, month, day, hour, minute, second, 0)  # Weekday is optional
    rtc.datetime(datetime)  # Set the RTC time
    rtc._OSF_reset()  # Reset the oscillator stop flag
    print("Time set successfully!")

