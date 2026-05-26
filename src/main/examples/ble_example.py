"""
ตัวอย่างการใช้งาน BLE Manager Module
แสดงวิธี import และใช้งานในโปรเจคของคุณ
"""

import sys
sys.path.append('/lib')

import asyncio
from ble.blemanager import BLEManager, BLEUART, BLESensor


# ========== ตัวอย่างที่ 1: BLE Server พื้นฐาน ==========
async def example_1_basic_server():
    """ตัวอย่างพื้นฐาน - BLE GATT Server"""
    print("=" * 50)
    print("ตัวอย่างที่ 1: BLE Server พื้นฐาน")
    print("=" * 50)
    
    # สร้าง BLE Manager
    ble = BLEManager(
        device_name="ESP32-C3",
        config_file="ble_config.json"
    )
    
    # บันทึก config (ถ้าต้องการ)
    ble.save_config(device_name="ESP32-C3", advertise_interval=100)
    
    # เริ่มต้น server
    print("\n🚀 กำลังเริ่ม BLE Server...")
    success = await ble.start_server()
    
    if success:
        print("✅ BLE Server เริ่มทำงานแล้ว")
        print(f"📊 สถานะ: {ble.get_status()}")
        
        # รอการเชื่อมต่อ
        print("\n⏳ รออุปกรณ์เชื่อมต่อ...")
        try:
            count = 0
            while True:
                await asyncio.sleep(1)
                count += 1
                
                if count % 10 == 0:
                    status = ble.get_status()
                    print(f"⏱️ รอ {count} วินาที | Connected: {status['connected']}")
                
                if ble.connected:
                    print("📱 มีอุปกรณ์เชื่อมต่อแล้ว!")
                    
                    # ส่งข้อมูลทดสอบ
                    ble.send_data(b"Hello from ESP32-C3!", notify=True)
        except KeyboardInterrupt:
            print("\n⏹️ หยุดโปรแกรม")
            await ble.stop()
    else:
        print("❌ ไม่สามารถเริ่ม BLE Server ได้")


# ========== ตัวอย่างที่ 2: BLE UART ==========
async def example_2_uart():
    """ตัวอย่าง BLE UART - สื่อสารแบบ Serial"""
    print("=" * 50)
    print("ตัวอย่างที่ 2: BLE UART Communication")
    print("=" * 50)
    
    # สร้าง BLE UART
    uart = BLEUART(device_name="ESP32-UART")
    
    # เริ่มต้น
    print("\n🚀 กำลังเริ่ม BLE UART...")
    await uart.begin()
    print("✅ BLE UART พร้อมแล้ว!")
    print("💡 ทดสอบส่งข้อมูลจากมือถือผ่าน BLE")
    
    try:
        while True:
            # ตรวจสอบข้อมูลที่ได้รับ
            if uart.any():
                data = uart.read()
                print(f"\n📥 ได้รับ: {data}")
                
                # ส่งตอบกลับ
                response = f"Echo: {data}"
                uart.println(response)
                print(f"📤 ส่งตอบ: {response}")
            
            await asyncio.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n⏹️ หยุดโปรแกรม")
        await uart.stop()


# ========== ตัวอย่างที่ 3: BLE Sensor ==========
async def example_3_sensor():
    """ตัวอย่าง BLE Sensor - ส่งค่าเซ็นเซอร์"""
    print("=" * 50)
    print("ตัวอย่างที่ 3: BLE Sensor Streaming")
    print("=" * 50)
    
    # สร้าง BLE Sensor
    sensor = BLESensor(device_name="ESP32-Sensor")
    
    # เริ่มต้น
    await sensor.begin()
    print("✅ BLE Sensor พร้อมแล้ว")
    
    # จำลองเซ็นเซอร์ (ใช้ ADC pin 0)
    try:
        from machine import ADC, Pin
        adc = ADC(Pin(0))
        adc.atten(ADC.ATTN_11DB)
        has_sensor = True
    except:
        print("⚠️ ไม่พบเซ็นเซอร์ กำลังใช้ค่าจำลอง")
        has_sensor = False
    
    # เริ่ม streaming
    print("\n📊 เริ่มส่งค่าเซ็นเซอร์ทุก 2 วินาที...")
    asyncio.create_task(sensor.start_streaming(interval=2))
    
    try:
        while True:
            # อ่านค่าเซ็นเซอร์
            if has_sensor:
                raw_value = adc.read()
                temperature = 25 + (raw_value * 0.01)  # จำลองอุณหภูมิ
                humidity = 50 + (raw_value * 0.005)  # จำลองความชื้น
            else:
                import random
                temperature = 25 + random.uniform(-2, 2)
                humidity = 50 + random.uniform(-5, 5)
            
            # อัปเดตค่าเซ็นเซอร์
            sensor.update_sensor(
                temperature=round(temperature, 2),
                humidity=round(humidity, 2),
                battery=85,
                timestamp=asyncio.get_event_loop().time()
            )
            
            # แสดงสถานะ
            if sensor.manager.connected:
                data = sensor.get_sensor_data()
                print(f"\n📊 Sensor Data: {data}")
            
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ หยุดโปรแกรม")
        sensor.stop_streaming()
        await sensor.stop()


# ========== ตัวอย่างที่ 4: BLE with Callbacks ==========
async def example_4_callbacks():
    """ตัวอย่างใช้ Callback Functions"""
    print("=" * 50)
    print("ตัวอย่างที่ 4: BLE with Callbacks")
    print("=" * 50)
    
    ble = BLEManager(device_name="ESP32-CB")
    
    # กำหนด callback functions
    def on_connect(conn_handle):
        print(f"\n✅ เชื่อมต่อแล้ว: handle={conn_handle}")
        ble.send_data(b"Welcome to ESP32-C3!", notify=True)
    
    def on_disconnect(conn_handle):
        print(f"\n❌ ขาดการเชื่อมต่อ: handle={conn_handle}")
        print("⏳ รอเชื่อมต่อใหม่...")
    
    def on_write(conn_handle, value_handle, data):
        try:
            text = data.decode("utf-8")
            print(f"\n📥 Write: {text}")
            
            # ส่งตอบกลับ
            response = f"Received: {text}"
            ble.send_data(response.encode(), notify=True)
        except:
            print(f"\n📥 Write (raw): {data}")
    
    def on_read(conn_handle, value_handle):
        print(f"\n📖 Read จาก characteristic")
    
    # ตั้งค่า callbacks
    ble.set_callback("on_connect", on_connect)
    ble.set_callback("on_disconnect", on_disconnect)
    ble.set_callback("on_write", on_write)
    ble.set_callback("on_read", on_read)
    
    # เริ่ม server
    print("\n🚀 กำลังเริ่ม BLE Server...")
    await ble.start_server()
    print("✅ BLE Server พร้อมแล้ว!")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️ หยุดโปรแกรม")
        await ble.stop()


# ========== ตัวอย่างที่ 5: BLE + WiFi พร้อมกัน ==========
async def example_5_ble_wifi():
    """ตัวอย่างใช้ BLE และ WiFi พร้อมกัน"""
    print("=" * 50)
    print("ตัวอย่างที่ 5: BLE + WiFi พร้อมกัน")
    print("=" * 50)
    
    # Import WiFi Manager
    from wifimanager import WiFiManager
    
    # เริ่มต้น WiFi
    print("\n📡 กำลังเชื่อมต่อ WiFi...")
    wifi = WiFiManager()
    wifi.load_config()
    
    if not wifi.get_config():
        print("⚠️ ยังไม่มี WiFi config")
        wifi.save_config(
            ssid="YOUR_WIFI_SSID",
            password="YOUR_WIFI_PASSWORD"
        )
    
    # เชื่อมต่อ WiFi
    # wifi_connected = await wifi.connect()
    wifi_connected = False  # Skip สำหรับตัวอย่าง
    
    # เริ่มต้น BLE
    print("\n🔵 กำลังเริ่ม BLE...")
    ble = BLEManager(device_name="ESP32-Combined")
    ble_success = await ble.start_server()
    
    # สร้าง tasks สำหรับรันพร้อมกัน
    tasks = []
    
    if wifi_connected:
        tasks.append(asyncio.create_task(wifi.keep_alive(), name="WiFi KeepAlive"))
    
    if ble_success:
        async def ble_monitor():
            while True:
                if ble.connected:
                    print("🔵 BLE Connected")
                await asyncio.sleep(5)
        
        tasks.append(asyncio.create_task(ble_monitor(), name="BLE Monitor"))
    
    # Main task
    async def main_loop():
        count = 0
        while True:
            count += 1
            
            # แสดงสถานะ
            wifi_status = "✅" if wifi_connected else "❌"
            ble_status = "✅" if ble.connected else "⏳"
            
            print(f"\n⏱️ [{count}s] WiFi: {wifi_status} | BLE: {ble_status}")
            
            await asyncio.sleep(5)
    
    tasks.append(asyncio.create_task(main_loop(), name="Main Loop"))
    
    try:
        print("\n🚀 เริ่มรันทั้งหมดพร้อมกัน...")
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n⏹️ หยุดโปรแกรม")
        ble.stop_keep_alive()
        if wifi_connected:
            wifi.stop_keep_alive()


# ========== ตัวอย่างที่ 6: BLE Control LED ==========
async def example_6_ble_led():
    """ตัวอย่าง BLE ควบคุม LED"""
    print("=" * 50)
    print("ตัวอย่างที่ 6: BLE Control LED")
    print("=" * 50)
    
    from machine import Pin
    
    # สร้าง LED pin (เปลี่ยน pin ตามที่ใช้)
    led = Pin(8, Pin.OUT)
    led_state = False
    
    ble = BLEManager(device_name="ESP32-LED")
    
    # Callback สำหรับจัดการคำสั่ง
    def on_command(text):
        nonlocal led_state
        
        text = text.strip().lower()
        print(f"\n📥 คำสั่ง: {text}")
        
        if text in ["on", "1", "open"]:
            led.value(1)
            led_state = True
            ble.send_data(b"LED ON", notify=True)
            print("💡 LED เปิดแล้ว")
        
        elif text in ["off", "0", "close"]:
            led.value(0)
            led_state = False
            ble.send_data(b"LED OFF", notify=True)
            print("💡 LED ปิดแล้ว")
        
        elif text in ["status", "?"]:
            state = "ON" if led_state else "OFF"
            ble.send_data(f"LED: {state}".encode(), notify=True)
            print(f"📊 สถานะ LED: {state}")
        
        else:
            ble.send_data(b"Unknown command. Use: on/off/status", notify=True)
            print("⚠️ คำสั่งไม่ถูกต้อง")
    
    # ตั้งค่า callback
    ble.set_callback("on_write", lambda c, v, d: on_command(d.decode("utf-8")))
    
    # เริ่ม server
    await ble.start_server()
    print("\n✅ BLE พร้อมแล้ว!")
    print("💡 ส่งคำสั่ง: on, off, status")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️ หยุดโปรแกรม")
        led.value(0)
        await ble.stop()


# ========== ตัวอย่างที่ 7: BLE iBeacon ==========
async def example_7_ibeacon():
    """ตัวอย่าง BLE iBeacon"""
    print("=" * 50)
    print("ตัวอย่างที่ 7: BLE iBeacon")
    print("=" * 50)
    
    ble = BLEManager(device_name="ESP32-iBeacon")
    
    if not await ble.init():
        print("❌ ไม่สามารถเปิด BLE")
        return
    
    # iBeacon configuration
    # หมายเหตุ: การใช้งานจริงต้องตั้งค่า iBeacon payload
    print("📡 กำลัง broadcasting iBeacon...")
    print("💡 ใช้แอปพลิเคชันเช่น 'BLE Scanner' เพื่อตรวจสอบ")
    
    try:
        while True:
            # Re-advertise เพื่อ broadcast ต่อไป
            ble._start_advertising()
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️ หยุดโปรแกรม")
        await ble.stop()


# ========== ตัวอย่างที่ 8: BLE GATT Client ==========
async def example_8_gatt_client():
    """ตัวอย่าง BLE GATT Client - เชื่อมต่อกับอุปกรณ์อื่น"""
    print("=" * 50)
    print("ตัวอย่างที่ 8: BLE GATT Client")
    print("=" * 50)
    
    ble = BLEManager(device_name="ESP32-Client")
    
    if not await ble.init():
        print("❌ ไม่สามารถเปิด BLE")
        return
    
    # Scan for devices
    print("\n🔍 กำลังสแกนอุปกรณ์ BLE...")
    # หมายเหตุ: การ scan ต้องใช้ gap_scan()
    
    # เชื่อมต่อกับอุปกรณ์ (ตัวอย่าง)
    target_name = "ESP32-Server"
    
    print(f"📡 กำลังเชื่อมต่อกับ: {target_name}")
    # หมายเหตุ: การเชื่อมต่อต้องใช่ gap_connect()
    
    # สำหรับเป็นตัวอย่างเท่านั้น
    print("⚠️ GATT Client ต้องใช้งานเพิ่มเติม")
    print("📖 ดูเอกสารเพิ่มเติมเกี่ยวกับการเชื่อมต่อเป็น client")


# ========== เริ่มต้นโปรแกรม ==========
if __name__ == "__main__":
    # เลือกตัวอย่างที่ต้องการรัน
    
    example_1_basic_server()
    # example_2_uart()
    # example_3_sensor()
    # example_4_callbacks()
    # example_5_ble_wifi()
    # example_6_ble_led()
    # example_7_ibeacon()
    # example_8_gatt_client()
