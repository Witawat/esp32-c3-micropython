"""
ตัวอย่างการใช้งาน WiFiManager Module
แสดงวิธี import และใช้งานในโปรเจคของคุณ
"""

import sys
sys.path.append('/lib')

import asyncio
from wifi.wifimanager import WiFiManager


# ========== ตัวอย่างที่ 1: ใช้งานพื้นฐาน ==========
async def example_1_basic():
    """ตัวอย่างพื้นฐาน - เชื่อมต่อ WiFi"""
    print("=" * 50)
    print("ตัวอย่างที่ 1: การใช้งานพื้นฐาน")
    print("=" * 50)
    
    # สร้าง WiFiManager instance
    wifi = WiFiManager()
    
    # บันทึก config ครั้งแรก (รันครั้งเดียว)
    wifi.save_config(
        ssid="YOUR_SSID",
        password="YOUR_PASSWORD"
    )
    
    # เชื่อมต่อ WiFi
    success = await wifi.connect()
    
    if success:
        print(f"✅ IP: {wifi.get_ip()}")
        print(wifi.get_connection_info())
    else:
        print("❌ เชื่อมต่อไม่สำเร็จ")


# ========== ตัวอย่างที่ 2: เชื่อมต่อโดยไม่ใช้ config file ==========
async def example_2_direct_connect():
    """เชื่อมต่อโดยตรงโดยไม่บันทึก config"""
    print("=" * 50)
    print("ตัวอย่างที่ 2: เชื่อมต่อโดยตรง")
    print("=" * 50)
    
    wifi = WiFiManager()
    
    # เชื่อมต่อโดยตรง (จะไม่บันทึก config)
    success = await wifi.connect(
        ssid="YOUR_SSID",
        password="YOUR_PASSWORD",
        timeout=10
    )
    
    if success:
        print(f"✅ IP: {wifi.get_ip()}")


# ========== ตัวอย่างที่ 3: Keep-Alive Mode ==========
async def example_3_keep_alive():
    """Keep-alive mode - ตรวจสอบการเชื่อมต่อตลอด"""
    print("=" * 50)
    print("ตัวอย่างที่ 3: Keep-Alive Mode")
    print("=" * 50)
    
    wifi = WiFiManager()
    
    # ตรวจสอบว่ามี config แล้วหรือยัง
    wifi.load_config()
    if not wifi.get_config():
        print("⚠️ ยังไม่มี config กำลังบันทึก...")
        wifi.save_config(
            ssid="YOUR_SSID",
            password="YOUR_PASSWORD",
            reconnect_interval=30  # ตรวจสอบทุก 30 วินาที
        )
    
    # เชื่อมต่อ
    await wifi.connect()
    
    # เริ่ม keep-alive (จะตรวจสอบการเชื่อมต่อตลอด)
    print("\n🔄 เริ่ม keep-alive mode...")
    print("   กด Ctrl+C เพื่อหยุด")
    
    try:
        await wifi.keep_alive()
    except KeyboardInterrupt:
        print("\n⏹️ หยุด keep-alive mode")
        wifi.stop_keep_alive()


# ========== ตัวอย่างที่ 4: Scan และเชื่อมต่อ ==========
async def example_4_scan_and_connect():
    """สแกน WiFi และเชื่อมต่อ"""
    print("=" * 50)
    print("ตัวอย่างที่ 4: Scan และเชื่อมต่อ")
    print("=" * 50)
    
    wifi = WiFiManager()
    
    # สแกน networks
    print("\n📡 กำลังสแกน WiFi...")
    networks = await wifi.scan_networks()
    
    # เลือก network ที่ต้องการ
    target_ssid = "YOUR_SSID"
    target_password = "YOUR_PASSWORD"
    
    # ตรวจสอบว่าพบ network หรือไม่
    found = any(net["ssid"] == target_ssid for net in networks)
    
    if found:
        print(f"\n✅ พบ '{target_ssid}' กำลังเชื่อมต่อ...")
        await wifi.connect(ssid=target_ssid, password=target_password)
    else:
        print(f"\n❌ ไม่พบ '{target_ssid}'")
        print("เครือข่ายที่พบ:")
        for net in networks:
            print(f"   - {net['ssid']} ({net['signal']} dBm)")


# ========== ตัวอย่างที่ 5: ใช้งานร่วมกับงานอื่นๆ ==========
async def example_5_with_other_tasks():
    """ใช้งาน WiFi พร้อมกับงานอื่นๆ"""
    print("=" * 50)
    print("ตัวอย่างที่ 5: ใช้งานร่วมกับงานอื่นๆ")
    print("=" * 50)
    
    wifi = WiFiManager()
    
    # โหลด config
    wifi.load_config()
    if not wifi.get_config():
        wifi.save_config(
            ssid="YOUR_SSID",
            password="YOUR_PASSWORD"
        )
    
    # สร้าง task สำหรับเชื่อมต่อ WiFi
    wifi_task = asyncio.create_task(wifi.connect(), name="WiFi Connect")
    
    # รอ WiFi เชื่อมต่อ
    await wifi_task
    
    if wifi.is_connected():
        print(f"\n✅ WiFi พร้อม! IP: {wifi.get_ip()}")
        
        # สร้าง task อื่นๆ ทำงานพร้อมกัน
        async def task_1():
            """ตัวอย่าง task 1"""
            count = 0
            while True:
                count += 1
                print(f"   📊 Task 1 ทำงานครั้งที่ {count}")
                await asyncio.sleep(5)
        
        async def task_2():
            """ตัวอย่าง task 2"""
            count = 0
            while True:
                count += 1
                print(f"   🔧 Task 2 ทำงานครั้งที่ {count}")
                await asyncio.sleep(3)
        
        async def wifi_keepalive():
            """WiFi keep-alive"""
            await wifi.keep_alive()
        
        # รันทุก tasks พร้อมกัน
        print("\n🚀 เริ่มรันทุก tasks พร้อมกัน...")
        try:
            await asyncio.gather(
                task_1(),
                task_2(),
                wifi_keepalive()
            )
        except KeyboardInterrupt:
            print("\n⏹️ หยุดโปรแกรม")
            wifi.stop_keep_alive()


# ========== ตัวอย่างที่ 6: ใช้ config หลายตัว ==========
async def example_6_multiple_configs():
    """ใช้ WiFi config หลายตัว"""
    print("=" * 50)
    print("ตัวอย่างที่ 6: Multiple Configs")
    print("=" * 50)
    
    # Config สำหรับที่บ้าน
    wifi = WiFiManager(config_file="wifi_config.json")
    
    # ตรวจสอบ config
    config = wifi.get_config()
    
    if not config:
        # ถ้ายังไม่มี config ให้บันทึก
        print("⚠️ ยังไม่มี config")
        
        # เลือกที่จะใช้ config ใด
        use_home = input("ใช้ WiFi บ้าน? (y/n): ").lower() == "y"
        
        if use_home:
            wifi.save_config(
                ssid="HOME_WIFI",
                password="HOME_PASSWORD"
            )
        else:
            wifi.save_config(
                ssid="OTHER_WIFI",
                password="OTHER_PASSWORD"
            )
    
    # เชื่อมต่อ
    await wifi.connect()
    
    if wifi.is_connected():
        print(f"✅ เชื่อมต่อสำเร็จ! IP: {wifi.get_ip()}")
    else:
        print("❌ เชื่อมต่อไม่สำเร็จ")


# ========== ตัวอย่างที่ 7: WiFi + HTTP Request ==========
async def example_7_wifi_http():
    """เชื่อมต่อ WiFi แล้วทำ HTTP request"""
    print("=" * 50)
    print("ตัวอย่างที่ 7: WiFi + HTTP Request")
    print("=" * 50)
    
    wifi = WiFiManager()
    wifi.load_config()
    
    if not wifi.get_config():
        wifi.save_config(
            ssid="YOUR_SSID",
            password="YOUR_PASSWORD"
        )
    
    # เชื่อมต่อ WiFi
    await wifi.connect()
    
    if not wifi.is_connected():
        print("❌ ไม่มี WiFi ไม่สามารถทำ HTTP request ได้")
        return
    
    # ทำ HTTP request (ตัวอย่าง)
    try:
        import urequests as requests
    except ImportError:
        try:
            import requests
        except ImportError:
            print("❌ ไม่พบ library requests")
            return
    
    print("\n🌐 กำลังดึงข้อมูลจาก http://example.com")

    try:
        response = requests.get("http://example.com")
        print(f"✅ Status: {response.status_code}")
        print(f"📄 Content-Length: {len(response.text)}")
        response.close()
    except Exception as e:
        print(f"❌ HTTP Error: {e}")


# ========== ตัวอย่างที่ 8: WiFi Status Monitor ==========
async def example_8_status_monitor():
    """WiFi Status Monitor"""
    print("=" * 50)
    print("ตัวอย่างที่ 8: WiFi Status Monitor")
    print("=" * 50)
    
    wifi = WiFiManager()
    wifi.load_config()
    
    if not wifi.get_config():
        wifi.save_config(
            ssid="YOUR_SSID",
            password="YOUR_PASSWORD",
            reconnect_interval=10
        )
    
    await wifi.connect()
    
    print("\n📊 เริ่มตรวจสอบสถานะ WiFi ทุก 5 วินาที...")
    
    try:
        while True:
            status = wifi.get_status()
            info = wifi.get_connection_info()
            
            print(f"\n{status}")
            if info["connected"]:
                print(f"   📡 SSID: {info['ssid']}")
                print(f"   🌐 IP: {info['ip']}")
                print(f"   🔗 Gateway: {info['gateway']}")
                print(f"   📍 MAC: {info['mac']}")
            
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("\n⏹️ หยุดโปรแกรม")


# ========== ตัวอย่างที่ 9: WiFi Portal (Web Configuration) ==========
async def example_9_wifi_portal():
    """WiFi Portal - ตั้งค่าผ่านหน้าเว็บ"""
    print("=" * 50)
    print("ตัวอย่างที่ 9: WiFi Configuration Portal")
    print("=" * 50)
    
    from wifimanager import WiFiPortal
    
    # สร้าง Portal
    portal = WiFiPortal(config_file="wifi_config.json")
    
    # เริ่ม Portal
    await portal.start_portal(
        ap_ssid="ESP32-Setup",
        ap_password="12345678"
    )


# ========== เริ่มต้นโปรแกรม ==========
if __name__ == "__main__":
    # เลือกตัวอย่างที่ต้องการรัน
    
    # example_1_basic()
    # example_2_direct_connect()
    # example_3_keep_alive()
    # example_4_scan_and_connect()
    # example_5_with_other_tasks()
    # example_6_multiple_configs()
    # example_7_wifi_http()
    # example_8_status_monitor()
    
    # 🌐 WiFi Portal - แนะนำตัวนี้!
    example_9_wifi_portal()
