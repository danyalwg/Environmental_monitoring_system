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
    """Sync RTC with an alternative NTP server and set the DS3231 time correctly."""
    try:
        ntptime.host = "asia.pool.ntp.org"  # Use reliable NTP server
        ntptime.settime()  # Sync ESP32 RTC with NTP
        
        rtc = RTC()
        year, month, day, _, hour, minute, second, _ = rtc.datetime()
        
        set_time(year, month, day, hour, minute, second)  # Set DS3231 RTC
        print(f"RTC updated with NTP time: {year} {month} {day} {hour} {minute} {second}")
    except Exception as e:
        print("Failed to sync time:", e)



if __name__ == "__main__":
    connect_wifi()
    sync_rtc_with_ntp()