import network
import ntptime
import time
from machine import RTC
from rtc import set_time

# Wi-Fi credentials
SSID = "._._._."
PASSWORD = "12345777"

def connect_wifi():
    """Connect to Wi-Fi."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    print("Connecting to Wi-Fi...")
    while not wlan.isconnected():
        time.sleep(1)
    print("Connected to Wi-Fi:", wlan.ifconfig())

def sync_rtc_with_ntp():
    """
    Sync the ESP32's RTC with an NTP server, then adjust the time by +5 hours
    (GMT+5) and set the DS3231 time accordingly.
    """
    try:
        # Specify a reliable NTP server
        ntptime.host = "asia.pool.ntp.org"
        # Sync the device's RTC to UTC
        ntptime.settime()
        
        # The ESP32's internal RTC is now set to UTC. Retrieve the current UTC time:
        now_utc = time.localtime()  # returns a tuple (year, month, day, hour, minute, second, weekday, yearday)
        
        # Convert this tuple to an epoch timestamp, add 5 hours, then convert back to a time tuple
        epoch_utc = time.mktime(now_utc)
        epoch_plus_5 = epoch_utc + (5 * 3600)  # 5 hours in seconds
        now_plus_5 = time.localtime(epoch_plus_5)
        
        # now_plus_5 = (year, month, day, hour, minute, second, weekday, yearday)
        # Set the DS3231 time to GMT+5
        set_time(now_plus_5[0], now_plus_5[1], now_plus_5[2],
                 now_plus_5[3], now_plus_5[4], now_plus_5[5])
        
        print("RTC updated to GMT+5:")
        print(f"{now_plus_5[0]}-{now_plus_5[1]:02d}-{now_plus_5[2]:02d} "
              f"{now_plus_5[3]:02d}:{now_plus_5[4]:02d}:{now_plus_5[5]:02d}")
    except Exception as e:
        print("Failed to sync time:", e)

if __name__ == "__main__":
    connect_wifi()
    sync_rtc_with_ntp()

