"""
WiFi Portal Example - ตัวอย่างการตั้งค่า WiFi ผ่านหน้าเว็บ
ใช้งาน WiFiPortal เพื่อสร้างหน้า Configuration แบบ offline
"""

import sys
sys.path.append('/lib')

import asyncio
from wifi.wifimanager import WiFiPortal, WiFiManager


# ========== ตัวอย่างที่ 1: Portal อย่างง่าย ==========
async def example_1_simple_portal():
    """ตัวอย่างง่ายที่สุด - เปิด Portal"""
    print("=" * 50)
    print("ตัวอย่างที่ 1: WiFi Portal อย่างง่าย")
    print("=" * 50)
    
    # สร้าง Portal
    portal = WiFiPortal()
    
    # เริ่ม Portal ด้วยค่า default
    # AP ชื่อ: ESP32-Setup
    # รหัส: 12345678
    await portal.start_portal()


# ========== ตัวอย่างที่ 2: Portal แบบกำหนดค่า ==========
async def example_2_custom_portal():
    """ตัวอย่าง Portal แบบกำหนดค่า"""
    print("=" * 50)
    print("ตัวอย่างที่ 2: Portal แบบกำหนดค่า")
    print("=" * 50)
    
    # สร้าง Portal แบบกำหนดค่า
    portal = WiFiPortal(
        config_file="my_wifi_config.json"  # ใช้ไฟล์ config ของตัวเอง
    )
    
    # เริ่ม Portal ด้วยชื่อและรหัสที่กำหนด
    await portal.start_portal(
        ap_ssid="MyESP32-Setup",        # ชื่อ AP
        ap_password="setup123"           # รหัสผ่าน (8 ตัวขึ้นไป)
    )


# ========== ตัวอย่างที่ 3: Portal + งานอื่น ==========
async def example_3_portal_with_tasks():
    """ตัวอย่าง Portal รันพร้อมกับงานอื่น"""
    print("=" * 50)
    print("ตัวอย่างที่ 3: Portal + Background Tasks")
    print("=" * 50)
    
    # สร้าง Portal
    portal = WiFiPortal()
    
    # เปิด AP Mode ก่อน
    if not await portal.start_ap_mode("ESP32-Setup", "12345678"):
        print("❌ ไม่สามารถเปิด AP Mode ได้")
        return
    
    # สร้าง HTTP Server
    portal._create_server()
    portal._running = True
    
    # สร้าง task อื่นๆ ทำงานพร้อมกัน
    async def led_blink():
        """ไฟกระพริบ"""
        try:
            from machine import Pin
            led = Pin(8, Pin.OUT)
            state = False
            
            while True:
                state = not state
                led.value(state)
                print(f"💡 LED {'ON' if state else 'OFF'}")
                await asyncio.sleep(1)
        except:
            # หากไม่มี LED pin
            while True:
                print("💡 LED Task Running...")
                await asyncio.sleep(1)
    
    async def sensor_read():
        """อ่านเซ็นเซอร์"""
        try:
            from machine import ADC, Pin
            adc = ADC(Pin(0))
            adc.atten(ADC.ATTN_11DB)
            
            while True:
                value = adc.read()
                print(f"📊 Sensor Value: {value}")
                await asyncio.sleep(2)
        except:
            while True:
                print("📊 Sensor Task Running...")
                await asyncio.sleep(2)
    
    async def portal_server():
        """Portal HTTP Server"""
        try:
            while portal._running:
                await asyncio.sleep_ms(100)
                
                try:
                    client, addr = portal.server.accept()
                    client.setblocking(False)
                    asyncio.create_task(portal._handle_client(client))
                except:
                    pass
        except Exception as e:
            print(f"Portal server error: {e}")
    
    # รันทั้งหมดพร้อมกัน
    print("\n✅ เริ่มทำงานทั้งหมด:")
    print("   🌐 Portal HTTP Server")
    print("   💡 LED Blink Task")
    print("   📊 Sensor Read Task")
    print(f"\n📱 เชื่อมต่อ WiFi: ESP32-Setup")
    print(f"   รหัส: 12345678")
    print(f"   เว็บ: http://192.168.4.1")
    
    try:
        await asyncio.gather(
            led_blink(),
            sensor_read(),
            portal_server()
        )
    except KeyboardInterrupt:
        print("\n⏹️ หยุดโปรแกรม")
        await portal.stop()


# ========== ตัวอย่างที่ 4: Portal แล้วตามด้วย STA Mode ==========
async def example_4_portal_then_sta():
    """ตัวอย่าง: เปิด Portal ก่อน แล้วค่อยเชื่อมต่อ WiFi"""
    print("=" * 50)
    print("ตัวอย่างที่ 4: Portal -> STA Mode")
    print("=" * 50)
    
    portal = WiFiPortal()
    
    # เปิด Portal ให้ผู้ใช้ตั้งค่า
    print("\n📱 กำลังเปิด Portal...")
    print("  กรุณาตั้งค่า WiFi ผ่านหน้าเว็บ")
    print("   (กด Ctrl+C เมื่อเสร็จแล้ว)")
    
    try:
        # เปิด Portal ชั่วคราว 60 วินาที
        await portal.start_portal(ap_ssid="ESP32-Setup", ap_password="12345678")
    except KeyboardInterrupt:
        print("\n⏹️ หยุด Portal")
        await portal.stop()
    
    # ตรวจสอบว่ามี config หรือไม่
    portal.wifi.load_config()
    
    if portal.wifi.get_config():
        print("\n✅ พบ WiFi config กำลังเชื่อมต่อ...")
        
        # เชื่อมต่อ WiFi ใน STA Mode
        success = await portal.wifi.connect()
        
        if success:
            print(f"✅ เชื่อมต่อสำเร็จ! IP: {portal.wifi.get_ip()}")
            
            # เริ่ม keep-alive
            await portal.wifi.keep_alive()
        else:
            print("❌ เชื่อมต่อไม่สำเร็จ")
    else:
        print("⚠️ ไม่มี WiFi config")
        print("   กรุณาตั้งค่าผ่าน Portal ก่อน")


# ========== ตัวอย่างที่ 5: Portal + Auto Reconnect ==========
async def example_5_portal_auto_reconnect():
    """ตัวอย่าง: Portal และ Auto Reconnect"""
    print("=" * 50)
    print("ตัวอย่างที่ 5: Portal + Auto Reconnect")
    print("=" * 50)
    
    portal = WiFiPortal()
    
    # เปิด AP Mode
    await portal.start_ap_mode("ESP32-Setup", "12345678")
    portal._create_server()
    portal._running = True
    
    # ตั้งค่า auto-reconnect หลังเชื่อมต่อ
    portal.wifi.config["auto_connect"] = True
    portal.wifi.config["reconnect"] = True
    portal.wifi.config["reconnect_interval"] = 30
    
    async def portal_handler():
        """จัดการ Portal"""
        while portal._running:
            await asyncio.sleep_ms(100)
            try:
                client, addr = portal.server.accept()
                client.setblocking(False)
                asyncio.create_task(portal._handle_client(client))
            except:
                pass
    
    async def monitor():
        """ตรวจสอบสถานะ"""
        while True:
            await asyncio.sleep(5)
            
            status = "✅" if portal.wifi.is_connected() else "❌"
            print(f"📊 WiFi Status: {status}")
            
            if portal.wifi.is_connected():
                print(f"   IP: {portal.wifi.get_ip()}")
    
    print("\n✅ Portal พร้อมแล้ว!")
    print("   ตั้งค่า WiFi แล้วระบบจะเชื่อมต่ออัตโนมัติ")
    
    try:
        await asyncio.gather(
            portal_handler(),
            monitor()
        )
    except KeyboardInterrupt:
        print("\n⏹️ หยุดโปรแกรม")
        await portal.stop()


# ========== ตัวอย่างที่ 6: สร้าง Portal ชั่วคราว ==========
async def example_6_temporary_portal():
    """ตัวอย่าง: เปิด Portal ชั่วคราว 30 วินาที"""
    print("=" * 50)
    print("ตัวอย่างที่ 6: Portal ชั่วคราว 30 วินาที")
    print("=" * 50)
    
    portal = WiFiPortal()
    
    # เปิด AP Mode
    if not await portal.start_ap_mode("ESP32-Setup", "12345678"):
        return
    
    portal._create_server()
    portal._running = True
    
    print("\n⏱️ Portal จะเปิดเป็นเวลา 30 วินาที")
    print("   กรุณาตั้งค่า WiFi ให้เร็วที่สุด!")
    
    # เปิด Portal 30 วินาที
    for i in range(30):
        await asyncio.sleep(1)
        if i % 5 == 0:
            print(f"   เหลือ {30-i} วินาที...")
        
        # ตรวจสอบว่ามี client หรือไม่
        try:
            client, addr = portal.server.accept()
            client.setblocking(False)
            print(f"📱 มี client เชื่อมต่อจาก {addr}")
            asyncio.create_task(portal._handle_client(client))
        except:
            pass
    
    print("\n⏰ หมดเวลา Portal!")
    await portal.stop()
    
    # ตรวจสอบว่าตั้งค่าสำเร็จหรือไม่
    portal.wifi.load_config()
    if portal.wifi.get_config():
        print("✅ พบ WiFi config!")
        success = await portal.wifi.connect()
        
        if success:
            print(f"✅ เชื่อมต่อสำเร็จ! IP: {portal.wifi.get_ip()}")
            await portal.wifi.keep_alive()
    else:
        print("❌ ไม่พบ WiFi config")


# ========== ตัวอย่างที่ 7: Portal + BLE ==========
async def example_7_portal_with_ble():
    """ตัวอย่าง: Portal + BLE พร้อมกัน"""
    print("=" * 50)
    print("ตัวอย่างที่ 7: Portal + BLE")
    print("=" * 50)
    
    try:
        from blemanager import BLEManager
    except ImportError:
        print("❌ ไม่พบ blemanager.py")
        return
    
    portal = WiFiPortal()
    ble = BLEManager(device_name="ESP32-C3")
    
    # เปิด Portal
    await portal.start_ap_mode("ESP32-Setup", "12345678")
    portal._create_server()
    portal._running = True
    
    # เปิด BLE
    await ble.start_server()
    
    async def portal_handler():
        while portal._running:
            await asyncio.sleep_ms(100)
            try:
                client, addr = portal.server.accept()
                client.setblocking(False)
                asyncio.create_task(portal._handle_client(client))
            except:
                pass
    
    async def ble_monitor():
        while True:
            if ble.connected:
                print("🔵 BLE Connected")
            await asyncio.sleep(5)
    
    print("\n✅ Portal + BLE พร้อมแล้ว!")
    print("   🌐 Portal: http://192.168.4.1")
    print("   🔵 BLE: ESP32-C3")
    
    try:
        await asyncio.gather(
            portal_handler(),
            ble_monitor()
        )
    except KeyboardInterrupt:
        print("\n⏹️ หยุดโปรแกรม")
        await portal.stop()
        await ble.stop()


# ========== เริ่มต้นโปรแกรม ==========
if __name__ == "__main__":
    # เลือกตัวอย่างที่ต้องการรัน
    
    # แนะนำตัวอย่างที่ 1 หรือ 2 สำหรับเริ่มใช้งาน
    example_1_simple_portal()
    # example_2_custom_portal()
    # example_3_portal_with_tasks()
    # example_4_portal_then_sta()
    # example_5_portal_auto_reconnect()
    # example_6_temporary_portal()
    # example_7_portal_with_ble()
