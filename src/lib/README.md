# ESP32 MicroPython Library Overview

เอกสารภาพรวมโครงสร้าง `lib/` สำหรับโปรเจกต์ ESP32 MicroPython

## โครงสร้างหมวดหลัก

| Folder | เนื้อหา |
|---|---|
| `wifi` | จัดการ WiFi STA/AP และ Config Portal |
| `ble` | BLE manager, UART over BLE, sensor streaming |
| `sensors` | ไดรเวอร์เซ็นเซอร์ 19 โมดูล (GPS, Battery Monitor เพิ่ม) |
| `display` | ไดรเวอร์จอ OLED/TFT/LCD/E-Paper + TJC HMI |
| `output` | อุปกรณ์เอาต์พุตและแอคชูเอเตอร์ (12 drivers — IR Remote เพิ่ม) |
| `input` | ปุ่ม, encoder, keypad, touch, joystick |
| `storage` | config manager, sd card, file logger |
| `mqtt` | MQTT manager |
| `http` | HTTP client/server |
| `websocket` | WebSocket client/server (RFC 6455) |
| `cloud` | ThingsBoard, Adafruit IO, Blynk, Firebase, AWS IoT |
| `system` | OTA, RTC, deepsleep, watchdog, sysinfo |

## การใช้งานร่วมกัน

ทุกตัวอย่างใช้รูปแบบเดียวกัน:

```python
import sys
sys.path.append('/lib')
```

จากนั้น import ตามหมวด:

```python
from wifi.wifimanager import WiFiManager
from sensors.dht import DHTSensor
from sensors.gps_nmea import GPSNMEA
from sensors.battery_monitor import BatteryMonitor
from mqtt.mqttmanager import MQTTManager
from websocket import WebSocketClient, WebSocketServer
from output.ir_remote import IRTransmitter, IRReceiver
```

## ลำดับการใช้งานที่แนะนำ

1. เชื่อมต่อ WiFi ด้วย `wifi`
2. อ่านค่าจาก `sensors`
3. แสดงผลผ่าน `display` หรือ `output`
4. ส่งข้อมูลด้วย `mqtt/http/cloud`
5. บันทึกข้อมูลผ่าน `storage`
6. ดูแลระบบด้วย `system`

## ตัวอย่างไฟล์ใน `main/examples`

- `wifi_example.py`
- `ble_example.py`
- `sensors_example.py`
- `display_example.py`
- `output_example.py`
- `input_example.py`
- `storage_example.py`
- `mqtt_example.py`
- `http_example.py`
- `websocket_example.py`
- `cloud_example.py`
- `system_example.py`

## หมายเหตุสำคัญ

- ESP32-C3/C6 ไม่มี TouchPad จึงไม่รองรับ `input/touch.py`
- AWS IoT (TLS) ใช้ RAM สูง ควรทดสอบหน่วยความจำก่อนใช้งานจริง
- หากนำขึ้นบอร์ด ให้ deploy โฟลเดอร์ `lib` ไปที่ `/lib` บนแฟลช
