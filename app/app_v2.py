#!/usr/bin/env python3
import sys
import time
import csv
import json
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QTabWidget, QLabel, QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem,
    QCheckBox, QLineEdit, QPushButton, QComboBox, QMessageBox, QPlainTextEdit, QToolTip
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import pyqtgraph as pg
import qdarkstyle

import serial
import serial.tools.list_ports
import simulate_sensors  # Your simulated sensors module

# Global mapping from warning sensor names to sensor data keys.
warning_sensor_mapping = {
    "MQ9 LPG": ("mq9", "LPG"),
    "MQ9 CO": ("mq9", "CO"),
    "MQ9 CH4": ("mq9", "CH4"),
    "MQ135 CO2": ("mq135", "CO2"),
    "MQ135 CO": ("mq135", "CO"),
    "MQ135 Alcohol": ("mq135", "alcohol"),
    "MQ135 NH4": ("mq135", "NH4"),
    "MQ135 Toluene": ("mq135", "toluene"),
    "MQ135 Acetone": ("mq135", "acetone"),
    "Temperature": ("bme280", "temperature"),
    "Pressure": ("bme280", "pressure"),
    "Humidity": ("bme280", "humidity"),
    "Dust Density": ("dust_sensor", "dust_density"),
    "Dust AQI": ("dust_sensor", "AQI"),
    "UV Index": ("uv_sensor", "uv_index"),
}

# ---------------------------
# Sensor Data Thread
# ---------------------------
class SensorDataThread(QThread):
    data_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Default source is "Simulated Sensors". When switching to Serial,
        # the receiver (which outputs full JSON packets) will be used.
        self.source = "Simulated Sensors"
        self.com_port = None
        self.baud_rate = None
        self.serial_conn = None

    def setSource(self, source):
        self.source = source
        # If switching to simulated data, close any open serial connection.
        if source == "Simulated Sensors" and self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None

    def setSerialParams(self, com_port, baud_rate):
        self.com_port = com_port
        try:
            self.baud_rate = int(baud_rate)
        except Exception as e:
            print("Invalid baud rate:", e)
            return
        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None
        try:
            self.serial_conn = serial.Serial(self.com_port, self.baud_rate, timeout=1)
            print(f"Opened serial port {self.com_port} at {self.baud_rate} baud.")
        except Exception as e:
            print("Error opening serial port:", e)
            self.serial_conn = None

    def run(self):
        while True:
            if self.source == "Simulated Sensors":
                sensor_data = simulate_sensors.simulate_sensor_packet()
                self.data_signal.emit(sensor_data)
            else:
                if self.serial_conn and self.serial_conn.is_open:
                    try:
                        # Read one line from the COM port
                        line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                        # Expect full JSON sensor packet (starting with '{')
                        if line and line.startswith('{'):
                            sensor_data = json.loads(line)
                            self.data_signal.emit(sensor_data)
                        # Otherwise, ignore the line (it may be boot messages)
                    except Exception as e:
                        print("Error reading from serial:", e)
                # If no serial connection is available, do nothing.
            self.msleep(1000)

# ---------------------------
# Real-Time Plot Widget with clear_data() method
# ---------------------------
class RealTimePlot(pg.PlotWidget):
    def __init__(self, sensor_group, param_key, label, unit, conversion_func=None, color='y', parent=None):
        date_axis = pg.DateAxisItem(orientation='bottom')
        super().__init__(axisItems={'bottom': date_axis}, parent=parent)
        self.sensor_group = sensor_group
        self.param_key = param_key
        self.label_text = label
        self.unit = unit
        self.conversion_func = conversion_func
        self.color = color
        self.setLabel('left', f"{label} ({unit})")
        self.setLabel('bottom', "Time")
        self.curve = self.plot(pen=color)
        self.enableAutoRange(axis='y', enable=True)
        self.xdata = []  # Time stamps
        self.ydata = []  # Sensor values
        self.max_points = 120  # Store last 2 minutes
        self.setMouseTracking(True)

    def update_data(self, sensor_data):
        t = time.time()
        try:
            raw_value = sensor_data[self.sensor_group][self.param_key]['value']
        except KeyError:
            raw_value = None
        if raw_value is not None:
            value = self.conversion_func(raw_value) if self.conversion_func else raw_value
            self.xdata.append(t)
            self.ydata.append(value)
            if len(self.xdata) > self.max_points:
                self.xdata = self.xdata[-self.max_points:]
                self.ydata = self.ydata[-self.max_points:]
            self.curve.setData(self.xdata, self.ydata)

    def clear_data(self):
        """Clear the stored data and reset the plot."""
        self.xdata = []
        self.ydata = []
        self.curve.setData([], [])

    def mouseMoveEvent(self, ev):
        pos = ev.pos()
        mousePoint = self.plotItem.vb.mapSceneToView(pos)
        x = mousePoint.x()
        y = mousePoint.y()
        QToolTip.showText(ev.globalPos(),
                          f"Time: {datetime.fromtimestamp(x).strftime('%H:%M:%S')}\nValue: {y:.2f}")
        super().mouseMoveEvent(ev)

# ---------------------------
# Group Widget for Plots with clear_plots() method
# ---------------------------
class PlotsGroupWidget(QWidget):
    def __init__(self, plot_definitions, columns=3, parent=None):
        super().__init__(parent)
        self.plot_definitions = plot_definitions
        self.plots = {}
        self.initUI(columns)

    def initUI(self, columns):
        layout = QGridLayout()
        for i, definition in enumerate(self.plot_definitions):
            name, sensor_group, param_key, label, unit, conv_func, color = definition
            plot_widget = RealTimePlot(sensor_group, param_key, label, unit, conv_func, color)
            self.plots[name] = plot_widget
            container = QWidget()
            vlayout = QVBoxLayout(container)
            vlayout.setContentsMargins(0, 0, 0, 0)
            vlayout.addWidget(plot_widget)
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignCenter)
            vlayout.addWidget(lbl)
            row = i // columns
            col = i % columns
            layout.addWidget(container, row, col)
        self.setLayout(layout)

    def update_data(self, sensor_data):
        for plot in self.plots.values():
            plot.update_data(sensor_data)

    def clear_plots(self):
        for plot in self.plots.values():
            plot.clear_data()

# ---------------------------
# Gas Sensors Plots Tab
# ---------------------------
class GasSensorsPlots(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        definitions = [
            ("MQ9 LPG",       "mq9",    "LPG",      "MQ9 LPG",       "ppm", None, 'r'),
            ("MQ9 CO",        "mq9",    "CO",       "MQ9 CO",        "ppm", None, 'g'),
            ("MQ9 CH4",       "mq9",    "CH4",      "MQ9 CH4",       "ppm", None, 'b'),
            ("MQ135 CO2",     "mq135",  "CO2",      "MQ135 CO2",     "ppm", None, 'c'),
            ("MQ135 CO",      "mq135",  "CO",       "MQ135 CO",      "ppm", None, 'm'),
            ("MQ135 Alcohol", "mq135",  "alcohol",  "MQ135 Alcohol", "ppm", None, 'y'),
            ("MQ135 NH4",     "mq135",  "NH4",      "MQ135 NH4",     "ppm", None, 'w'),
            ("MQ135 Toluene", "mq135",  "toluene",  "MQ135 Toluene", "ppm", None, 'orange'),
            ("MQ135 Acetone", "mq135",  "acetone",  "MQ135 Acetone", "ppm", None, 'purple')
        ]
        self.group_widget = PlotsGroupWidget(definitions, columns=3)
        layout = QVBoxLayout()
        layout.addWidget(self.group_widget)
        self.setLayout(layout)

    def update_data(self, sensor_data):
        self.group_widget.update_data(sensor_data)

# ---------------------------
# Environmental Sensors Plots Tab
# ---------------------------
class EnvironmentalSensorsPlots(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        definitions = [
            ("Temperature",  "bme280",      "temperature",  "Temperature",  "°C", None, 'r'),
            ("Pressure",     "bme280",      "pressure",     "Pressure",     "hPa", None, 'g'),
            ("Humidity",     "bme280",      "humidity",     "Humidity",     "%",   None, 'b'),
            ("Dust Density", "dust_sensor", "dust_density", "Dust Density", "µg/m³", None, 'c'),
            ("Dust AQI",     "dust_sensor", "AQI",        "Dust AQI",     "AQI", None, 'm'),
            ("UV Index",     "uv_sensor",   "uv_index",     "UV Index",     "index", None, 'lime')
        ]
        self.group_widget = PlotsGroupWidget(definitions, columns=3)
        layout = QVBoxLayout()
        layout.addWidget(self.group_widget)
        self.setLayout(layout)

    def update_data(self, sensor_data):
        self.group_widget.update_data(sensor_data)

# ---------------------------
# Plots Tab (contains sub-tabs for Gas and Environmental sensors)
# ---------------------------
class PlotsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.tabs = QTabWidget()
        self.gas_tab = GasSensorsPlots()
        self.env_tab = EnvironmentalSensorsPlots()
        self.tabs.addTab(self.gas_tab, "Gas Sensors")
        self.tabs.addTab(self.env_tab, "Environmental Sensors")
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def update_data(self, sensor_data):
        self.gas_tab.update_data(sensor_data)
        self.env_tab.update_data(sensor_data)

    def clear_plots(self):
        self.gas_tab.group_widget.clear_plots()
        self.env_tab.group_widget.clear_plots()

# ---------------------------
# Digital Tab (displays sensor values in text)
# ---------------------------
class DigitalTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.setStyleSheet("""
            QLabel { font-size: 10pt; }
            QGroupBox { font-size: 12pt; margin-top: 5px; border: 1px solid gray; border-radius: 5px; padding: 5px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; }
        """)

    def initUI(self):
        layout = QVBoxLayout()

        # RTC Group
        rtc_group = QGroupBox("RTC")
        rtc_layout = QFormLayout()
        self.label_date = QLabel("N/A")
        self.label_time = QLabel("N/A")
        rtc_layout.addRow("Date:", self.label_date)
        rtc_layout.addRow("Time:", self.label_time)
        rtc_group.setLayout(rtc_layout)
        layout.addWidget(rtc_group)

        # BME280 Group (moved directly after RTC)
        bme_group = QGroupBox("BME280")
        bme_layout = QFormLayout()
        self.label_temp = QLabel("N/A")
        self.label_pressure = QLabel("N/A")
        self.label_humidity = QLabel("N/A")
        bme_layout.addRow("Temperature (°C):", self.label_temp)
        bme_layout.addRow("Pressure (hPa):", self.label_pressure)
        bme_layout.addRow("Humidity (%):", self.label_humidity)
        bme_group.setLayout(bme_layout)
        layout.addWidget(bme_group)

        # MQ9 Group
        mq9_group = QGroupBox("MQ9")
        mq9_layout = QFormLayout()
        self.label_mq9_lpg = QLabel("N/A")
        self.label_mq9_co = QLabel("N/A")
        self.label_mq9_ch4 = QLabel("N/A")
        mq9_layout.addRow("LPG (ppm):", self.label_mq9_lpg)
        mq9_layout.addRow("CO (ppm):", self.label_mq9_co)
        mq9_layout.addRow("CH4 (ppm):", self.label_mq9_ch4)
        mq9_group.setLayout(mq9_layout)
        layout.addWidget(mq9_group)

        # MQ135 Group
        mq135_group = QGroupBox("MQ135")
        mq135_layout = QFormLayout()
        self.label_mq135_co2 = QLabel("N/A")
        self.label_mq135_co = QLabel("N/A")
        self.label_mq135_alcohol = QLabel("N/A")
        self.label_mq135_nh4 = QLabel("N/A")
        self.label_mq135_toluene = QLabel("N/A")
        self.label_mq135_acetone = QLabel("N/A")
        mq135_layout.addRow("CO2 (ppm):", self.label_mq135_co2)
        mq135_layout.addRow("CO (ppm):", self.label_mq135_co)
        mq135_layout.addRow("Alcohol (ppm):", self.label_mq135_alcohol)
        mq135_layout.addRow("NH4 (ppm):", self.label_mq135_nh4)
        mq135_layout.addRow("Toluene (ppm):", self.label_mq135_toluene)
        mq135_layout.addRow("Acetone (ppm):", self.label_mq135_acetone)
        mq135_group.setLayout(mq135_layout)
        layout.addWidget(mq135_group)

        # Dust Sensor Group
        dust_group = QGroupBox("Dust Sensor")
        dust_layout = QFormLayout()
        self.label_dust_adc = QLabel("N/A")
        self.label_dust_voltage = QLabel("N/A")
        self.label_dust_density = QLabel("N/A")
        self.label_dust_aqi = QLabel("N/A")
        dust_layout.addRow("Raw ADC:", self.label_dust_adc)
        dust_layout.addRow("Voltage:", self.label_dust_voltage)
        dust_layout.addRow("Dust Density (µg/m³):", self.label_dust_density)
        dust_layout.addRow("AQI:", self.label_dust_aqi)
        dust_group.setLayout(dust_layout)
        layout.addWidget(dust_group)

        # UV Sensor Group
        uv_group = QGroupBox("UV Sensor")
        uv_layout = QFormLayout()
        self.label_uv_intensity = QLabel("N/A")
        self.label_uv_index = QLabel("N/A")
        uv_layout.addRow("UV Intensity (mW/cm²):", self.label_uv_intensity)
        uv_layout.addRow("UV Index:", self.label_uv_index)
        uv_group.setLayout(uv_layout)
        layout.addWidget(uv_group)

        layout.addStretch()
        self.setLayout(layout)

        # Mapping for warning color updates.
        self.digital_labels = {
            "MQ9 LPG": self.label_mq9_lpg,
            "MQ9 CO": self.label_mq9_co,
            "MQ9 CH4": self.label_mq9_ch4,
            "MQ135 CO2": self.label_mq135_co2,
            "MQ135 CO": self.label_mq135_co,
            "MQ135 Alcohol": self.label_mq135_alcohol,
            "MQ135 NH4": self.label_mq135_nh4,
            "MQ135 Toluene": self.label_mq135_toluene,
            "MQ135 Acetone": self.label_mq135_acetone,
            "Temperature": self.label_temp,
            "Pressure": self.label_pressure,
            "Humidity": self.label_humidity,
            "Dust Density": self.label_dust_density,
            "Dust AQI": self.label_dust_aqi,
            "UV Index": self.label_uv_index
        }

    def update_data(self, data):
        rtc = data.get("rtc", {})
        self.label_date.setText(rtc.get('date', 'N/A'))
        self.label_time.setText(rtc.get('time', 'N/A'))

        # MQ9 sensors
        self.label_mq9_lpg.setText(f"{data.get('mq9', {}).get('LPG', {}).get('value', 'N/A')} ppm")
        self.label_mq9_co.setText(f"{data.get('mq9', {}).get('CO', {}).get('value', 'N/A')} ppm")
        self.label_mq9_ch4.setText(f"{data.get('mq9', {}).get('CH4', {}).get('value', 'N/A')} ppm")

        # MQ135 sensors
        self.label_mq135_co2.setText(f"{data.get('mq135', {}).get('CO2', {}).get('value', 'N/A')} ppm")
        self.label_mq135_co.setText(f"{data.get('mq135', {}).get('CO', {}).get('value', 'N/A')} ppm")
        self.label_mq135_alcohol.setText(f"{data.get('mq135', {}).get('alcohol', {}).get('value', 'N/A')} ppm")
        self.label_mq135_nh4.setText(f"{data.get('mq135', {}).get('NH4', {}).get('value', 'N/A')} ppm")
        self.label_mq135_toluene.setText(f"{data.get('mq135', {}).get('toluene', {}).get('value', 'N/A')} ppm")
        self.label_mq135_acetone.setText(f"{data.get('mq135', {}).get('acetone', {}).get('value', 'N/A')} ppm")

        # BME280 sensors
        self.label_temp.setText(f"{data.get('bme280', {}).get('temperature', {}).get('value', 'N/A')} °C")
        self.label_pressure.setText(f"{data.get('bme280', {}).get('pressure', {}).get('value', 'N/A')} hPa")
        self.label_humidity.setText(f"{data.get('bme280', {}).get('humidity', {}).get('value', 'N/A')} %")

        # Dust sensor
        self.label_dust_adc.setText(f"{data.get('dust_sensor', {}).get('raw_adc', {}).get('value', 'N/A')} counts")
        self.label_dust_voltage.setText(f"{data.get('dust_sensor', {}).get('voltage', {}).get('value', 'N/A')} V")
        self.label_dust_density.setText(f"{data.get('dust_sensor', {}).get('dust_density', {}).get('value', 'N/A')} µg/m³")
        self.label_dust_aqi.setText(f"{data.get('dust_sensor', {}).get('AQI', {}).get('value', 'N/A')} AQI")

        # UV sensor
        self.label_uv_intensity.setText(f"{data.get('uv_sensor', {}).get('uv_intensity', {}).get('value', 'N/A')} mW/cm²")
        self.label_uv_index.setText(f"{data.get('uv_sensor', {}).get('uv_index', {}).get('value', 'N/A')} index")

# ---------------------------
# Warning Setup Tab
# ---------------------------
class WarningSetupTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.warning_settings = {}
        self.warning_sensors = [
            "MQ9 LPG", "MQ9 CO", "MQ9 CH4",
            "MQ135 CO2", "MQ135 CO", "MQ135 Alcohol",
            "MQ135 NH4", "MQ135 Toluene", "MQ135 Acetone",
            "Temperature", "Pressure", "Humidity",
            "Dust Density", "Dust AQI", "UV Index"
        ]
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.table = QTableWidget(len(self.warning_sensors), 4)
        self.table.setHorizontalHeaderLabels(["Sensor", "Enable Warning", "Lower Limit", "Upper Limit"])
        for row, sensor in enumerate(self.warning_sensors):
            item = QTableWidgetItem(sensor)
            item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 0, item)
            checkbox = QCheckBox()
            self.table.setCellWidget(row, 1, checkbox)
            lower_edit = QLineEdit()
            self.table.setCellWidget(row, 2, lower_edit)
            upper_edit = QLineEdit()
            self.table.setCellWidget(row, 3, upper_edit)
        self.table.resizeColumnsToContents()
        layout.addWidget(self.table)
        self.apply_btn = QPushButton("Apply Warning Settings")
        self.apply_btn.setStyleSheet("font-size: 14pt; padding: 10px;")
        self.apply_btn.clicked.connect(self.applySettings)
        layout.addWidget(self.apply_btn)
        self.setLayout(layout)

    def applySettings(self):
        settings = {}
        for row in range(self.table.rowCount()):
            sensor = self.table.item(row, 0).text()
            enabled = self.table.cellWidget(row, 1).isChecked()
            lower_text = self.table.cellWidget(row, 2).text().strip()
            upper_text = self.table.cellWidget(row, 3).text().strip()
            lower = float(lower_text) if lower_text != "" else -float('inf')
            upper = float(upper_text) if upper_text != "" else float('inf')
            settings[sensor] = {"enabled": enabled, "lower": lower, "upper": upper}
        self.warning_settings = settings
        msg_lines = []
        for sensor, setting in settings.items():
            lower_str = str(setting["lower"]) if setting["lower"] != -float('inf') else "None"
            upper_str = str(setting["upper"]) if setting["upper"] != float('inf') else "None"
            status = "Enabled" if setting["enabled"] else "Disabled"
            msg_lines.append(f"{sensor}: {status}, Lower Limit: {lower_str}, Upper Limit: {upper_str}")
        msg = "\n".join(msg_lines)
        QMessageBox.information(self, "Warning Settings Applied", msg)

    def getWarningSettings(self):
        return self.warning_settings

# ---------------------------
# Logs Tab
# ---------------------------
class LogsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        layout.addWidget(self.log_edit)
        self.setLayout(layout)

    def appendLog(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_edit.appendPlainText(f"[{timestamp}] {message}")

    def getLogText(self):
        return self.log_edit.toPlainText()

# ---------------------------
# Export Tab
# ---------------------------
class ExportTab(QWidget):
    def __init__(self, digital_tab, logs_tab, parent=None):
        super().__init__(parent)
        self.digital_tab = digital_tab
        self.logs_tab = logs_tab
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.export_sensor_btn = QPushButton("Export Current Sensor Data (CSV)")
        self.export_sensor_btn.setStyleSheet("font-size: 12pt; padding: 5px;")
        self.export_sensor_btn.clicked.connect(self.exportSensorData)
        layout.addWidget(self.export_sensor_btn)
        self.export_logs_btn = QPushButton("Export Logs (CSV)")
        self.export_logs_btn.setStyleSheet("font-size: 12pt; padding: 5px;")
        self.export_logs_btn.clicked.connect(self.exportLogs)
        layout.addWidget(self.export_logs_btn)
        layout.addStretch()
        self.setLayout(layout)

    def exportSensorData(self):
        data = {
            "Date": self.digital_tab.label_date.text(),
            "Time": self.digital_tab.label_time.text(),
            "MQ9 LPG": self.digital_tab.label_mq9_lpg.text(),
            "MQ9 CO": self.digital_tab.label_mq9_co.text(),
            "MQ9 CH4": self.digital_tab.label_mq9_ch4.text(),
            "MQ135 CO2": self.digital_tab.label_mq135_co2.text(),
            "MQ135 CO": self.digital_tab.label_mq135_co.text(),
            "MQ135 Alcohol": self.digital_tab.label_mq135_alcohol.text(),
            "MQ135 NH4": self.digital_tab.label_mq135_nh4.text(),
            "MQ135 Toluene": self.digital_tab.label_mq135_toluene.text(),
            "MQ135 Acetone": self.digital_tab.label_mq135_acetone.text(),
            "Temperature": self.digital_tab.label_temp.text(),
            "Pressure": self.digital_tab.label_pressure.text(),
            "Humidity": self.digital_tab.label_humidity.text(),
            "Dust Density": self.digital_tab.label_dust_density.text(),
            "Dust AQI": self.digital_tab.label_dust_aqi.text(),
            "UV Index": self.digital_tab.label_uv_index.text()
        }
        folder = r"C:\Users\danya\Desktop\SensorDataExports"
        if not os.path.exists(folder):
            os.makedirs(folder)
        filename = os.path.join(folder, f"SensorData_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        try:
            with open(filename, mode="w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Sensor", "Value"])
                for key, value in data.items():
                    writer.writerow([key, value])
            QMessageBox.information(self, "Export Sensor Data", f"Data exported to {filename}")
        except Exception as e:
            QMessageBox.warning(self, "Export Sensor Data", f"Failed to export data: {e}")

    def exportLogs(self):
        log_text = self.logs_tab.getLogText()
        folder = r"C:\Users\danya\Desktop\SensorLogsExports"
        if not os.path.exists(folder):
            os.makedirs(folder)
        filename = os.path.join(folder, f"SensorLogs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        try:
            with open(filename, mode="w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Timestamp", "Log Message"])
                for line in log_text.splitlines():
                    if line.startswith("[") and "]" in line:
                        timestamp, message = line.split("]", 1)
                        writer.writerow([timestamp.strip("["), message.strip()])
            QMessageBox.information(self, "Export Logs", f"Logs exported to {filename}")
        except Exception as e:
            QMessageBox.warning(self, "Export Logs", f"Failed to export logs: {e}")

# ---------------------------
# Connectivity Tab
# ---------------------------
class ConnectivityTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QFormLayout()
        self.com_port_combo = QComboBox()
        self.com_port_combo.addItem("Simulated Sensors")
        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                self.com_port_combo.addItem(port.device)
        except Exception as e:
            print("Error detecting COM ports:", e)
            self.com_port_combo.addItems(["COM1", "COM2", "COM3", "COM4"])
        layout.addRow("Select Data Source:", self.com_port_combo)
        self.baud_rate_combo = QComboBox()
        common_baud_rates = ["9600", "19200", "38400", "57600", "115200"]
        self.baud_rate_combo.addItems(common_baud_rates)
        self.baud_rate_combo.setEnabled(False)
        layout.addRow("Baud Rate:", self.baud_rate_combo)
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setStyleSheet("font-size: 12pt; padding: 5px;")
        layout.addRow(self.connect_btn)
        self.setLayout(layout)
        self.com_port_combo.currentIndexChanged.connect(self.comPortChanged)

    def comPortChanged(self, index):
        if self.com_port_combo.currentText() == "Simulated Sensors":
            self.baud_rate_combo.setEnabled(False)
        else:
            self.baud_rate_combo.setEnabled(True)

# ---------------------------
# Main Application Window (SensorDashboard)
# ---------------------------
class SensorDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Environmental Monitoring Dashboard")
        self.resize(1200, 800)
        self.initUI()
        # Track current warning state per sensor.
        self.warning_state = {sensor: False for sensor in warning_sensor_mapping}
        self.startSensorThread()

    def initUI(self):
        self.tabs = QTabWidget()
        self.digital_tab = DigitalTab()
        self.plots_tab = PlotsTab()
        self.warning_tab = WarningSetupTab()
        self.connectivity_tab = ConnectivityTab()
        self.logs_tab = LogsTab()
        self.export_tab = ExportTab(self.digital_tab, self.logs_tab)
        self.tabs.addTab(self.digital_tab, "Digital Values")
        self.tabs.addTab(self.plots_tab, "Plots")
        self.tabs.addTab(self.warning_tab, "Warning Setup")
        self.tabs.addTab(self.connectivity_tab, "Connectivity")
        self.tabs.addTab(self.logs_tab, "Logs")
        self.tabs.addTab(self.export_tab, "Export")
        self.setCentralWidget(self.tabs)
        # Connect the "Connect" button.
        self.connectivity_tab.connect_btn.clicked.connect(self.onConnectClicked)

    def startSensorThread(self):
        self.sensor_thread = SensorDataThread()
        self.sensor_thread.data_signal.connect(self.updateData)
        # Start with the default source: Simulated Sensors.
        self.sensor_thread.setSource("Simulated Sensors")
        self.sensor_thread.start()

    def onConnectClicked(self):
        new_source = self.connectivity_tab.com_port_combo.currentText()
        previous_source = self.sensor_thread.source if hasattr(self.sensor_thread, 'source') else "Unknown"
        # Log the source change.
        log_message = f"Data source changed from '{previous_source}' to '{new_source}'."
        self.logs_tab.appendLog(log_message)
        # Clear existing plots.
        self.plots_tab.clear_plots()
        if new_source == "Simulated Sensors":
            self.sensor_thread.setSource("Simulated Sensors")
            QMessageBox.information(self, "Connectivity", f"Switched to {new_source}")
        else:
            baud_rate = self.connectivity_tab.baud_rate_combo.currentText()
            self.sensor_thread.setSource(new_source)
            self.sensor_thread.setSerialParams(new_source, baud_rate)
            QMessageBox.information(self, "Connectivity", f"Connected to device: {new_source} at {baud_rate}")

    def updateData(self, sensor_data):
        self.digital_tab.update_data(sensor_data)
        self.plots_tab.update_data(sensor_data)
        # Check warnings.
        warning_settings = self.warning_tab.getWarningSettings()
        for sensor, settings in warning_settings.items():
            if not settings.get("enabled", False):
                if sensor in self.digital_tab.digital_labels:
                    self.digital_tab.digital_labels[sensor].setStyleSheet("")
                self.warning_state[sensor] = False
                continue
            if sensor not in warning_sensor_mapping:
                continue
            group, key = warning_sensor_mapping[sensor]
            try:
                value = sensor_data[group][key]['value']
            except KeyError:
                continue
            try:
                numeric_value = float(value)
            except Exception:
                continue
            lower = settings["lower"]
            upper = settings["upper"]
            if numeric_value < lower or numeric_value > upper:
                if not self.warning_state[sensor]:
                    self.warning_state[sensor] = True
                    msg = (f"Warning: {sensor} value {numeric_value} is out of bounds "
                           f"(Limit: {lower if lower != -float('inf') else 'None'} - "
                           f"{upper if upper != float('inf') else 'None'}).")
                    self.logs_tab.appendLog(msg)
                    QMessageBox.warning(self, "Sensor Warning", msg)
                    if sensor in self.digital_tab.digital_labels:
                        self.digital_tab.digital_labels[sensor].setStyleSheet("color: red;")
            else:
                if self.warning_state[sensor]:
                    self.warning_state[sensor] = False
                    if sensor in self.digital_tab.digital_labels:
                        self.digital_tab.digital_labels[sensor].setStyleSheet("")

# ---------------------------
# Run the Application
# ---------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = SensorDashboard()
    window.show()
    sys.exit(app.exec_())
