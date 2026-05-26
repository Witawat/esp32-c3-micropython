"""
ตัวอย่างการใช้งาน asyncio บน ESP32-C3
แสดงการทำงานแบบ asynchronous หลายงานพร้อมกัน
"""

import asyncio
from machine import Pin, ADC
import network


# ========== ตัวอย่างที่ 1: ไฟกระพริบ ==========
class LEDBlinker:
    """ควบคุมการกระพริบของ LED"""
    
    def __init__(self, pin_number=8, blink_interval=0.5):
        self.led = Pin(pin_number, Pin.OUT)
        self.interval = blink_interval
        self.running = False
    
    async def start(self):
        """เริ่มกระพริบ LED แบบ async"""
        self.running = True
        print(f"🔴 LED เริ่มกระพริบที่ pin {self.led}")
        
        while self.running:
            self.led.value(1)
            await asyncio.sleep(self.interval)
            self.led.value(0)
            await asyncio.sleep(self.interval)
    
    def stop(self):
        """หยุดกระพริบ"""
        self.running = False


# ========== ตัวอย่างที่ 2: อ่านค่าเซ็นเซอร์ ==========
class SensorReader:
    """อ่านค่าจากเซ็นเซอร์แบบ periodic"""
    
    def __init__(self, pin_number=0, read_interval=2):
        self.adc = ADC(Pin(pin_number))
        self.adc.atten(ADC.ATTN_11DB)
        self.interval = read_interval
        self.running = False
    
    async def start(self):
        """เริ่มอ่านเซ็นเซอร์"""
        self.running = True
        print(f"📊 เริ่มอ่านเซ็นเซอร์ที่ pin {self.adc}")
        
        while self.running:
            try:
                value = self.adc.read()
                voltage = value * (3.3 / 4095)
                print(f"📈 ค่าเซ็นเซอร์: {value} ({voltage:.2f}V)")
            except Exception as e:
                print(f"❌ ข้อผิดพลาดในการอ่านเซ็นเซอร์: {e}")
            
            await asyncio.sleep(self.interval)
    
    def stop(self):
        """หยุดอ่านเซ็นเซอร์"""
        self.running = False


# ========== ตัวอย่างที่ 3: WiFi Connection ==========
class WiFiManager:
    """จัดการการเชื่อมต่อ WiFi"""
    
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password
        self.wlan = network.WLAN(network.STA_IF)
        self.connected = False
    
    async def connect(self):
        """เชื่อมต่อ WiFi แบบ async"""
        print(f"📡 กำลังเชื่อมต่อ WiFi: {self.ssid}")
        
        self.wlan.active(True)
        self.wlan.connect(self.ssid, self.password)
        
        # รอการเชื่อมต่อ (timeout 15 วินาที)
        timeout = 15
        while timeout > 0:
            if self.wlan.isconnected():
                self.connected = True
                ip = self.wlan.ifconfig()[0]
                print(f"✅ เชื่อมต่อ WiFi สำเร็จ! IP: {ip}")
                return True
            
            await asyncio.sleep(1)
            timeout -= 1
            print(f"⏳ รอเชื่อมต่อ... ({15-timeout} วินาที)")
        
        print("❌ ไม่สามารถเชื่อมต่อ WiFi ได้")
        return False
    
    async def keep_alive(self, check_interval=30):
        """ตรวจสอบการเชื่อมต่อเป็นระยะ"""
        self.running = True
        
        while self.running:
            if not self.wlan.isconnected():
                print("⚠️ WiFi ขาด! กำลังเชื่อมต่อใหม่...")
                self.connected = False
                await self.connect()
            
            await asyncio.sleep(check_interval)
    
    def disconnect(self):
        """ยกเลิกการเชื่อมต่อ"""
        self.running = False
        if self.wlan.isconnected():
            self.wlan.disconnect()
            print("👋 ยกเลิกการเชื่อมต่อ WiFi แล้ว")


# ========== ตัวอย่างที่ 4: HTTP Server อย่างง่าย ==========
async def simple_http_server():
    """HTTP server อย่างง่ายด้วย asyncio"""
    try:
        import usocket as socket
    except ImportError:
        import socket
    
    addr = socket.getaddrinfo('0.0.0.0', 80, 0, socket.SOCK_STREAM)[0][-1]
    s = socket.socket()
    s.setblocking(False)  # ทำให้เป็น non-blocking
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    
    print(f"🌐 HTTP server เริ่มทำงานที่ port 80")
    
    while True:
        try:
            # รอการเชื่อมต่อแบบ non-blocking
            await asyncio.sleep_ms(100)
            # หมายเหตุ: สำหรับ production ควรใช้ uasyncio.start_server()
        except Exception as e:
            print(f"❌ HTTP server error: {e}")
            await asyncio.sleep(1)


# ========== ตัวอย่างที่ 5: งานหลายๆ อย่างรันพร้อมกัน ==========
async def main():
    """ฟังก์ชันหลัก - รันทุกงานพร้อมกัน"""
    
    print("=" * 50)
    print("🚀 เริ่มตัวอย่าง asyncio บน ESP32-C3")
    print("=" * 50)
    
    # สร้าง instances
    led_blinker = LEDBlinker(pin_number=8, blink_interval=1)
    sensor = SensorReader(pin_number=0, read_interval=3)
    wifi = WiFiManager("your_ssid", "your_password")
    
    # สร้าง tasks สำหรับรันพร้อมกัน
    tasks = [
        asyncio.create_task(led_blinker.start(), name="LED Blinker"),
        asyncio.create_task(sensor.start(), name="Sensor Reader"),
        # asyncio.create_task(wifi.connect(), name="WiFi Connect"),
        # asyncio.create_task(wifi.keep_alive(), name="WiFi Keep Alive"),
    ]
    
    # แสดงสถานะ
    print(f"\n✅ สร้าง {len(tasks)} tasks สำเร็จ")
    print(f"📋 Tasks: {[task.get_name() for task in tasks]}")
    
    # รัน tasks ทั้งหมดพร้อมกัน (จะรันตลอดไป)
    try:
        print("\n🔄 เริ่มรัน tasks ทั้งหมดพร้อมกัน...")
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n⏹️ ได้รับสัญญาณหยุด")
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
    finally:
        # Cleanup
        print("\n🧹 กำลัง cleanup...")
        led_blinker.stop()
        sensor.stop()
        
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        print("✅ Cleanup เสร็จสิ้น")


# ========== ฟังก์ชันสำหรับทดสอบแต่ละตัว ==========
async def test_led_only():
    """ทดสอบ LED เพียงอย่างเดียว"""
    led = LEDBlinker(pin_number=8, blink_interval=0.5)
    try:
        await led.start()
    except KeyboardInterrupt:
        led.stop()

async def test_sensor_only():
    """ทดสอบเซ็นเซอร์เพียงอย่างเดียว"""
    sensor = SensorReader(pin_number=0, read_interval=1)
    try:
        await sensor.start()
    except KeyboardInterrupt:
        sensor.stop()

async def test_wifi_only():
    """ทดสอบ WiFi เพียงอย่างเดียว"""
    wifi = WiFiManager("your_ssid", "your_password")
    try:
        connected = await wifi.connect()
        if connected:
            await wifi.keep_alive()
    except KeyboardInterrupt:
        wifi.disconnect()


# ========== เริ่มต้นโปรแกรม ==========
if __name__ == "__main__":
    # เลือกฟังก์ชันที่ต้องการรัน
    
    # รันทุกอย่างพร้อมกัน
    asyncio.run(main())
    
    # หรือทดสอบทีละตัว (comment บรรทัดบนก่อน):
    # asyncio.run(test_led_only())
    # asyncio.run(test_sensor_only())
    # asyncio.run(test_wifi_only())
