"""
BLE Manager Module สำหรับ ESP32-C3
จัดการการเชื่อมต่อ Bluetooth Low Energy (BLE)
รองรับการใช้งานแบบ GATT Server/Client

วิธีใช้งาน:
    from blemanager import BLEManager
    
    # สร้าง BLE Server
    ble = BLEManager(device_name="ESP32-C3")
    await ble.start_server()
    
    # หรือใช้แบบง่าย
    ble = BLEManager()
    await ble.start_simple_server()
"""

import asyncio
import json
import struct
import machine
from machine import Pin, ADC

try:
    from storage.config_mgr import JsonConfigManager
except ImportError:
    JsonConfigManager = None


try:
    import bluetooth
    HAS_BLUETOOTH = True
except ImportError:
    HAS_BLUETOOTH = False
    print("⚠️ ไม่พบ module bluetooth - กำลังใช้ mock mode")


# ========== BLE UUID Standards ==========
class BLEUUID:
    """มาตรฐาน UUID สำหรับ BLE Services"""
    
    # Standard Services
    DEVICE_INFO = "0000180A-0000-1000-8000-00805F9B34FB"
    BATTERY = "0000180F-0000-1000-8000-00805F9B34FB"
    
    # Custom Services
    UART_SERVICE = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
    UART_RX = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
    UART_TX = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
    
    SENSOR_SERVICE = "0000181A-0000-1000-8000-00805F9B34FB"
    ENVIRONMENTAL = "00002A6E-0000-1000-8000-00805F9B34FB"


class BLEManager:
    """
    จัดการการเชื่อมต่อ Bluetooth Low Energy
    """
    
    def __init__(self, device_name="ESP32-C3", config_file="ble_config.json"):
        """
        สร้าง instance ของ BLEManager
        
        Args:
            device_name (str): ชื่ออุปกรณ์ BLE
            config_file (str): ชื่อไฟล์ configuration
        """
        self.device_name = device_name
        self.config_file = config_file
        self.ble = None
        self.connected = False
        self.config = {}
        self._config_mgr = JsonConfigManager(config_file) if JsonConfigManager else None
        self.services = {}
        self.callbacks = {}
        self._running = False
        
        # BLE connection handle
        self.conn_handle = None
        
        # โหลด config
        self.load_config()
    
    def load_config(self):
        """โหลด configuration จากไฟล์ JSON"""
        if self._config_mgr:
            self.config = self._config_mgr.load(default={})
            if "device_name" in self.config:
                self.device_name = self.config["device_name"]
            return

        try:
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
                if "device_name" in self.config:
                    self.device_name = self.config["device_name"]
        except OSError:
            self.config = {}
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการโหลด config: {e}")
            self.config = {}
    
    def save_config(self, **kwargs):
        """บันทึก configuration ลงไฟล์ JSON"""
        self.config.update(kwargs)

        if self._config_mgr:
            ok = self._config_mgr.save(self.config)
            if ok:
                print(f"💾 บันทึก BLE config ลง {self.config_file}")
            return ok
        
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f)
                print(f"💾 บันทึก BLE config ลง {self.config_file}")
                return True
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการบันทึก config: {e}")
            return False
    
    def is_available(self):
        """ตรวจสอบว่าอุปกรณ์รองรับ BLE หรือไม่"""
        return HAS_BLUETOOTH
    
    async def init(self):
        """เริ่มต้น BLE"""
        if not HAS_BLUETOOTH:
            print("⚠️ BLE ไม่พร้อมใช้งาน - ใช้ mock mode")
            return False
        
        try:
            self.ble = bluetooth.BLE()
            self.ble.active(True)
            print(f"✅ BLE เปิดใช้งานแล้ว: {self.device_name}")
            return True
        except Exception as e:
            print(f"❌ ไม่สามารถเปิด BLE: {e}")
            return False
    
    async def start_server(self, services=None):
        """
        เริ่ม BLE GATT Server
        
        Args:
            services (list): รายการ services ที่ต้องการ
        
        Returns:
            bool: True หากสำเร็จ
        """
        if not self.ble:
            if not await self.init():
                return False
        
        # กำหนด services
        if services is None:
            services = self._get_default_services()
        
        try:
            # Register services
            for service in services:
                self._register_service(service)
            
            # Start advertising
            self._start_advertising()
            
            # Register IRQ handler
            self.ble.irq(self._ble_irq_handler)  # type: ignore[union-attr]
            
            self._running = True
            print(f"📡 BLE Server เริ่มทำงาน: {self.device_name}")
            return True
            
        except Exception as e:
            print(f"❌ ไม่สามารถเริ่ม BLE Server: {e}")
            return False
    
    async def start_simple_server(self):
        """เริ่ม BLE Server แบบง่ายพร้อม UART service"""
        uart_service = {
            "uuid": BLEUUID.UART_SERVICE,
            "characteristics": [
                {
                    "uuid": BLEUUID.UART_RX,
                    "properties": bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE,
                    "callback": self._on_uart_rx
                },
                {
                    "uuid": BLEUUID.UART_TX,
                    "properties": bluetooth.FLAG_NOTIFY,
                    "callback": None
                }
            ]
        }
        
        return await self.start_server([uart_service])
    
    def _get_default_services(self):
        """ดึง services เริ่มต้น"""
        return [
            {
                "uuid": BLEUUID.DEVICE_INFO,
                "characteristics": [
                    {
                        "uuid": "00002A29-0000-1000-8000-00805F9B34FB",  # Manufacturer
                        "properties": bluetooth.FLAG_READ,
                        "value": "ESP32-C3"
                    },
                    {
                        "uuid": "00002A26-0000-1000-8000-00805F9B34FB",  # Firmware
                        "properties": bluetooth.FLAG_READ,
                        "value": "1.0.0"
                    }
                ]
            }
        ]
    
    def _register_service(self, service):
        """ลงทะเบียน service"""
        service_uuid = service["uuid"]
        characteristics = service.get("characteristics", [])
        
        # TODO: ลงทะเบียน service กับ BLE stack
        print(f"   📋 ลงทะเบียน service: {service_uuid}")
        
        self.services[service_uuid] = {
            "handle": len(self.services),
            "characteristics": characteristics
        }
    
    def _start_advertising(self):
        """เริ่ม advertising"""
        if not self.ble:
            return
        
        # สร้าง advertising payload
        name = self.device_name.encode("utf-8")
        
        # Advertising parameters
        adv_data = bytes([
            0x02, 0x01, 0x06,  # LE General Discoverable Mode
            len(name) + 1, 0x09,  # Complete Local Name
        ]) + name
        
        self.ble.gap_advertise(100, adv_data)
        print(f"📢 Advertising: {self.device_name}")
    
    def stop_advertising(self):
        """หยุด advertising"""
        if self.ble:
            self.ble.gap_advertise(None)
            print("⏹️ หยุด advertising")
    
    def _ble_irq_handler(self, event, data):
        """จัดการ BLE events"""
        if event == 1:  # _IRQ_CENTRAL_CONNECT
            self.conn_handle, _, _ = data
            self.connected = True
            print(f"✅ เชื่อมต่อแล้ว: handle={self.conn_handle}")
            
            if "on_connect" in self.callbacks:
                self.callbacks["on_connect"](self.conn_handle)
        
        elif event == 2:  # _IRQ_CENTRAL_DISCONNECT
            self.conn_handle, _ = data
            self.connected = False
            print(f"❌ ขาดการเชื่อมต่อ: handle={self.conn_handle}")
            
            # เริ่ม advertising ใหม่
            self._start_advertising()
            
            if "on_disconnect" in self.callbacks:
                self.callbacks["on_disconnect"](self.conn_handle)
        
        elif event == 3:  # _IRQ_GATTS_WRITE
            conn_handle, value_handle = data
            value = self.ble.gatts_read(value_handle)  # type: ignore[union-attr]
            
            if "on_write" in self.callbacks:
                self.callbacks["on_write"](conn_handle, value_handle, value)
        
        elif event == 20:  # _IRQ_GATTS_INDICATE_DONE
            if "on_indicate_done" in self.callbacks:
                self.callbacks["on_indicate_done"]()
    
    def set_callback(self, event_name, callback):
        """ตั้งค่า callback function
        
        Args:
            event_name (str): ชื่อ event (on_connect, on_disconnect, on_write, on_read)
            callback (function): ฟังก์ชัน callback
        """
        self.callbacks[event_name] = callback
    
    def send_data(self, data, notify=True, indicate=False):
        """ส่งข้อมูลไปยังอุปกรณ์ที่เชื่อมต่อ
        
        Args:
            data (bytes): ข้อมูลที่ต้องการส่ง
            notify (bool): True เพื่อใช้ notification
            indicate (bool): True เพื่อใช้ indication
        
        Returns:
            bool: True หากส่งสำเร็จ
        """
        if not self.connected or not self.ble:
            return False
        
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            
            # TODO: หา characteristic handle ที่ถูกต้อง
            # สำหรับตอนนี้ใช้ dummy handle
            char_handle = 2  # Dummy handle
            
            if notify:
                self.ble.gatts_notify(self.conn_handle, char_handle, data)
            elif indicate:
                self.ble.gatts_indicate(self.conn_handle, char_handle, data)
            
            return True
        except Exception as e:
            print(f"❌ ไม่สามารถส่งข้อมูล: {e}")
            return False
    
    def send_uart(self, text):
        """ส่งข้อมูลผ่าน UART TX
        
        Args:
            text (str): ข้อความที่ต้องการส่ง
        
        Returns:
            bool: True หากส่งสำเร็จ
        """
        return self.send_data(text, notify=True)
    
    def _on_uart_rx(self, conn_handle, value_handle, data):
        """จัดการข้อมูลที่ได้รับจาก UART RX"""
        try:
            text = data.decode("utf-8")
            print(f"📥 ได้รับ: {text}")
            
            if "on_uart_rx" in self.callbacks:
                self.callbacks["on_uart_rx"](text)
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการถอดข้อมูล: {e}")
    
    async def disconnect(self):
        """ยกเลิกการเชื่อมต่อ"""
        if self.connected and self.conn_handle is not None:
            if self.ble:
                self.ble.gap_disconnect(self.conn_handle)
                self.connected = False
                print("👋 ยกเลิกการเชื่อมต่อ BLE")
    
    async def stop(self):
        """หยุด BLE Server"""
        self._running = False
        await self.disconnect()
        
        if self.ble:
            self.ble.active(False)
            print("⏹️ หยุด BLE")
    
    def get_status(self):
        """ดึงสถานะ BLE
        
        Returns:
            dict: สถานะ BLE
        """
        return {
            "active": self.ble.active() if self.ble else False,
            "connected": self.connected,
            "device_name": self.device_name,
            "services": len(self.services),
            "conn_handle": self.conn_handle
        }
    
    def __str__(self):
        """String representation"""
        status = self.get_status()
        return f"BLEManager(name={status['device_name']}, connected={status['connected']})"


# ========== UART BLE Service ==========
class BLEUART:
    """
    BLE UART Service แบบง่าย
    สำหรับการสื่อสารแบบ serial ผ่าน BLE
    """
    
    def __init__(self, device_name="ESP32-C3-UART"):
        """
        สร้าง BLE UART instance
        
        Args:
            device_name (str): ชื่ออุปกรณ์
        """
        self.manager = BLEManager(device_name=device_name)
        self.rx_buffer = []
        self.tx_callback = None
    
    async def begin(self, baudrate=115200):
        """เริ่มต้น BLE UART
        
        Args:
            baudrate (int): Baud rate (ไม่ใช่สำหรับ BLE แต่มีไว้เพื่อ compatibility)
        """
        self.manager.set_callback("on_uart_rx", callback=self._on_receive)
        return await self.manager.start_simple_server()
    
    def _on_receive(self, data):
        """จัดการข้อมูลที่ได้รับ"""
        self.rx_buffer.append(data)
        
        if self.tx_callback:
            self.tx_callback(data)
    
    def read(self):
        """อ่านข้อมูลจาก buffer
        
        Returns:
            str: ข้อมูลที่ได้รับ หรือ None
        """
        if self.rx_buffer:
            data = "".join(self.rx_buffer)
            self.rx_buffer.clear()
            return data
        return None
    
    def readline(self):
        """อ่านข้อมูลทีละบรรทัด
        
        Returns:
            str: บรรทัดที่ได้รับ หรือ None
        """
        for i, data in enumerate(self.rx_buffer):
            if "\n" in data:
                line = "".join(self.rx_buffer[:i+1])
                self.rx_buffer = self.rx_buffer[i+1:]
                return line.strip()
        return None
    
    def write(self, data):
        """ส่งข้อมูล
        
        Args:
            data (str): ข้อมูลที่ต้องการส่ง
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.manager.send_data(data, notify=True)
    
    def println(self, text):
        """ส่งข้อมูลพร้อม newline
        
        Args:
            text (str): ข้อความที่ต้องการส่ง
        """
        self.write(text + "\n")
    
    def any(self):
        """ตรวจสอบว่ามีข้อมูลใน buffer หรือไม่
        
        Returns:
            bool: True หากมีข้อมูล
        """
        return len(self.rx_buffer) > 0
    
    async def stop(self):
        """หยุด BLE UART"""
        await self.manager.stop()


# ========== BLE Sensor Service ==========
class BLESensor:
    """
    BLE Sensor Service
    สำหรับอ่านและส่งค่าเซ็นเซอร์ผ่าน BLE
    """
    
    def __init__(self, device_name="ESP32-C3-Sensor"):
        """
        สร้าง BLE Sensor Instance
        
        Args:
            device_name (str): ชื่ออุปกรณ์
        """
        self.manager = BLEManager(device_name=device_name)
        self.sensor_data = {}
        self.update_interval = 5
        self._running = False
    
    async def begin(self):
        """เริ่มต้น BLE Sensor Service"""
        sensor_service = {
            "uuid": BLEUUID.SENSOR_SERVICE,
            "characteristics": [
                {
                    "uuid": BLEUUID.ENVIRONMENTAL,
                    "properties": bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,
                    "callback": None
                }
            ]
        }
        
        return await self.manager.start_server([sensor_service])
    
    def update_sensor(self, **kwargs):
        """อัปเดตค่าเซ็นเซอร์
        
        Args:
            **kwargs: ค่าเซ็นเซอร์ที่ต้องการอัปเดต
        """
        self.sensor_data.update(kwargs)
    
    def get_sensor_data(self):
        """ดึงค่าเซ็นเซอร์ปัจจุบัน
        
        Returns:
            dict: ค่าเซ็นเซอร์
        """
        return self.sensor_data.copy()
    
    async def start_streaming(self, interval=5):
        """เริ่มส่งค่าเซ็นเซอร์อัตโนมัติ
        
        Args:
            interval (int): ช่วงเวลาในการส่ง (วินาที)
        """
        self.update_interval = interval
        self._running = True
        
        print(f"📊 เริ่มส่งค่าเซ็นเซอร์ทุก {interval} วินาที")
        
        while self._running:
            if self.manager.connected:
                # แปลงข้อมูลเป็น bytes
                data = json.dumps(self.sensor_data)
                self.manager.send_data(data, notify=True)
            
            await asyncio.sleep(interval)
    
    def stop_streaming(self):
        """หยุดส่งค่าเซ็นเซอร์"""
        self._running = False
    
    async def stop(self):
        """หยุด BLE Sensor"""
        self.stop_streaming()
        await self.manager.stop()


# ========== ตัวอย่างการใช้งาน ==========

async def example_basic_ble():
    """ตัวอย่างพื้นฐาน - BLE Server"""
    print("=" * 50)
    print("ตัวอย่างที่ 1: BLE Server พื้นฐาน")
    print("=" * 50)
    
    ble = BLEManager(device_name="ESP32-C3-Test")
    
    # เริ่มต้น server
    success = await ble.start_server()
    
    if success:
        print("✅ BLE Server เริ่มทำงานแล้ว")
        print(f"สถานะ: {ble.get_status()}")
        
        # รอการเชื่อมต่อ
        try:
            while True:
                await asyncio.sleep(1)
                if ble.connected:
                    print("📱 มีอุปกรณ์เชื่อมต่อ!")
        except KeyboardInterrupt:
            print("\n⏹️ หยุดโปรแกรม")
            await ble.stop()


async def example_uart_ble():
    """ตัวอย่าง BLE UART"""
    print("=" * 50)
    print("ตัวอย่างที่ 2: BLE UART")
    print("=" * 50)
    
    uart = BLEUART(device_name="ESP32-UART")
    
    # เริ่มต้น
    await uart.begin()
    print("📡 BLE UART พร้อมแล้ว")
    
    try:
        while True:
            # ตรวจสอบข้อมูลที่ได้รับ
            if uart.any():
                data = uart.read()
                print(f"📥 ได้รับ: {data}")
                
                # ส่งตอบกลับ
                uart.println(f"Echo: {data}")
            
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        print("\n⏹️ หยุดโปรแกรม")
        await uart.stop()


async def example_sensor_ble():
    """ตัวอย่าง BLE Sensor"""
    print("=" * 50)
    print("ตัวอย่างที่ 3: BLE Sensor")
    print("=" * 50)
    
    sensor = BLESensor(device_name="ESP32-Sensor")
    
    # เริ่มต้น
    await sensor.begin()
    
    # จำลองค่าเซ็นเซอร์
    adc = ADC(Pin(0))
    adc.atten(ADC.ATTN_11DB)
    
    # เริ่ม streaming
    asyncio.create_task(sensor.start_streaming(interval=2))
    
    try:
        while True:
            # อ่านค่าเซ็นเซอร์
            temp = adc.read() * 0.1  # จำลองอุณหภูมิ
            humidity = adc.read() * 0.05  # จำลองความชื้น
            
            # อัปเดตค่า
            sensor.update_sensor(
                temperature=round(temp, 2),
                humidity=round(humidity, 2),
                battery=85
            )
            
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️ หยุดโปรแกรม")
        sensor.stop_streaming()
        await sensor.stop()


async def example_with_callbacks():
    """ตัวอย่างใช้ Callbacks"""
    print("=" * 50)
    print("ตัวอย่างที่ 4: BLE with Callbacks")
    print("=" * 50)
    
    ble = BLEManager(device_name="ESP32-CB")
    
    # ตั้งค่า callbacks
    def on_connect(conn_handle):
        print(f"✅ เชื่อมต่อแล้ว: {conn_handle}")
    
    def on_disconnect(conn_handle):
        print(f"❌ ขาดการเชื่อมต่อ: {conn_handle}")
    
    def on_write(conn_handle, value_handle, data):
        text = data.decode("utf-8")
        print(f"📥 Write: {text}")
    
    ble.set_callback("on_connect", on_connect)
    ble.set_callback("on_disconnect", on_disconnect)
    ble.set_callback("on_write", on_write)
    
    # เริ่ม server
    await ble.start_server()
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️ หยุดโปรแกรม")
        await ble.stop()


# ========== เริ่มต้นโปรแกรม ==========
if __name__ == "__main__":
    # เลือกตัวอย่างที่ต้องการรัน
    
    asyncio.run(example_basic_ble())
    # asyncio.run(example_uart_ble())
    # asyncio.run(example_sensor_ble())
    # asyncio.run(example_with_callbacks())
