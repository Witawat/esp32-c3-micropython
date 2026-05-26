"""
REPL Examples — ตัวอย่างการใช้งาน REPL library บน ESP32-C3

ตัวอย่างในไฟล์นี้:
    1. Basic CommandDispatcher — dispatcher พื้นฐาน (ไม่ต้องใช้ network)
    2. TCP REPL — รับคำสั่งผ่าน WiFi TCP Socket (telnet)
    3. UART REPL — รับคำสั่งผ่าน Serial port
    4. BLE REPL — รับคำสั่งผ่าน Bluetooth UART
    5. Multi-Transport — TCP + BLE ทำงานพร้อมกัน

วิธีรัน:
    import asyncio
    asyncio.run(example_1_basic_dispatcher())
"""

import asyncio
import sys
sys.path.append('/lib')

from repl.command_dispatcher import CommandDispatcher
from repl.tcp_repl import TCPRepl
from repl.uart_repl import UARTRepl
from repl.ble_repl import BLERepl
from repl.web_repl import WebREPL


# ============================================================
# ตัวอย่างที่ 1 — Basic CommandDispatcher (ไม่ต้องใช้ network)
# ============================================================

async def example_1_basic_dispatcher():
    """
    🟢 พื้นฐาน — สร้าง dispatcher ลงทะเบียน command และทดสอบ dispatch

    ใช้ได้แบบ standalone ไม่ต้องใช้ WiFi หรือ BLE
    เหมาะสำหรับทดสอบ logic คำสั่งก่อน deploy จริง
    """
    print("=== ตัวอย่างที่ 1: Basic CommandDispatcher ===")

    # สร้าง dispatcher
    dispatcher = CommandDispatcher(
        prompt="esp32> ",
        exec_enabled=False,  # ปิด raw exec โดย default
    )

    # ลงทะเบียน command ด้วย decorator
    @dispatcher.command("ping", "ทดสอบการตอบสนอง")
    def ping(*args):
        return "pong 🏓"

    @dispatcher.command("led", "เปิด/ปิด LED  |  ใช้: led <on|off>")
    def led(*args):
        state = args[0].lower() if args else "on"
        if state == "on":
            # Pin(2, Pin.OUT).value(1)  # uncommend บน hardware จริง
            return "✅ LED เปิดแล้ว"
        elif state == "off":
            # Pin(2, Pin.OUT).value(0)
            return "✅ LED ปิดแล้ว"
        return "❌ ใช้: led on  หรือ  led off"

    @dispatcher.command("temp", "อ่านอุณหภูมิจำลอง  |  ใช้: temp read")
    def temp(*args):
        import random
        value = 20.0 + random.random() * 15
        return f"🌡 อุณหภูมิ: {value:.1f}°C"

    # ทดสอบ dispatch
    print(dispatcher.dispatch("help"))
    print(dispatcher.dispatch("ping"))
    print(dispatcher.dispatch("led on"))
    print(dispatcher.dispatch("led off"))
    print(dispatcher.dispatch("temp read"))
    print(dispatcher.dispatch("mem"))
    print(dispatcher.dispatch("unknowncmd"))


# ============================================================
# ตัวอย่างที่ 2 — TCP REPL (WiFi)
# ============================================================

async def example_2_tcp_repl():
    """
    🟡 ระดับกลาง — TCP REPL ผ่าน WiFi

    วิธีเชื่อมต่อ:
        telnet <ESP32-IP> 8266
        nc <ESP32-IP> 8266
        หรือเปิด PuTTY → Raw mode → ระบุ IP และ port 8266
    """
    print("=== ตัวอย่างที่ 2: TCP REPL ===")

    # เชื่อมต่อ WiFi ก่อน
    from wifi.wifimanager import WiFiManager
    wifi = WiFiManager()
    ok = await wifi.connect("MySSID", "MyPassword")
    if not ok:
        print("❌ WiFi เชื่อมต่อไม่ได้")
        return

    ip = wifi.get_ip()
    print(f"✅ WiFi IP: {ip}")

    # สร้าง dispatcher
    dispatcher = CommandDispatcher(
        prompt="tcp> ",
        welcome=f"ESP32 TCP REPL — IP: {ip}\r\nพิมพ์ 'help' เพื่อดูคำสั่ง",
    )

    # ลงทะเบียน commands
    @dispatcher.command("status", "แสดงสถานะระบบ")
    def status(*args):
        import gc
        return (
            f"📊 สถานะระบบ\r\n"
            f"  WiFi: {'✅ เชื่อมต่อ' if wifi.is_connected() else '❌ ไม่ได้เชื่อมต่อ'}\r\n"
            f"  IP: {wifi.get_ip()}\r\n"
            f"  Free RAM: {gc.mem_free()} bytes"
        )

    @dispatcher.command("reset", "รีสตาร์ท ESP32")
    def reset_cmd(*args):
        import machine
        # ส่ง response ก่อน reset
        asyncio.create_task(_delayed_reset())
        return "🔄 กำลัง reset ใน 1 วินาที..."

    async def _delayed_reset():
        await asyncio.sleep(1)
        import machine
        machine.reset()

    # เริ่ม TCP REPL (รับ 1 client พร้อมกัน)
    repl = TCPRepl(dispatcher, port=8266)
    await repl.start()

    print(f"📡 รอ telnet {ip} 8266")
    # keep running
    while True:
        await asyncio.sleep(10)


async def example_2b_tcp_repl_with_password():
    """
    🔴 มืออาชีพ — TCP REPL พร้อม password authentication
    """
    from wifi.wifimanager import WiFiManager
    wifi = WiFiManager()
    await wifi.connect("MySSID", "MyPassword")

    dispatcher = CommandDispatcher(prompt="secure> ")

    @dispatcher.command("hello", "ทักทาย")
    def hello(*args):
        name = args[0] if args else "World"
        return f"สวัสดี {name}! 👋"

    # password="secret123" — client ต้องส่ง password ก่อนถึงจะใช้งานได้
    repl = TCPRepl(dispatcher, port=8266, password="secret123")
    await repl.start()

    print(f"🔒 TCP REPL (protected) — telnet {wifi.get_ip()} 8266")
    while True:
        await asyncio.sleep(10)


# ============================================================
# ตัวอย่างที่ 3 — UART REPL (Serial)
# ============================================================

async def example_3_uart_repl():
    """
    🟡 ระดับกลาง — UART REPL ผ่าน serial port

    การต่อสาย:
        ESP32-C3 GPIO21 (TX) → USB-Serial RX
        ESP32-C3 GPIO20 (RX) → USB-Serial TX
        GND → GND

    เปิด serial terminal:
        Windows: PuTTY → Serial → COM port → 115200 baud
        macOS/Linux: screen /dev/ttyUSB1 115200
                     minicom -D /dev/ttyUSB1 -b 115200

    หมายเหตุ: ใช้ UART1 (ไม่ใช่ UART0) เพราะ UART0 ใช้โดย MicroPython REPL อยู่แล้ว
    """
    print("=== ตัวอย่างที่ 3: UART REPL ===")

    dispatcher = CommandDispatcher(
        prompt="uart> ",
        welcome="ESP32 UART REPL\r\nต่อสาย TX=GPIO21, RX=GPIO20, GND\r\nพิมพ์ 'help'",
    )

    @dispatcher.command("gpio", "อ่าน/เขียน GPIO  |  ใช้: gpio read <pin>  หรือ  gpio write <pin> <0|1>")
    def gpio_cmd(*args):
        from machine import Pin
        if len(args) < 2:
            return "❌ ใช้: gpio read <pin>  หรือ  gpio write <pin> <0|1>"
        action = args[0].lower()
        try:
            pin_num = int(args[1])
        except ValueError:
            return "❌ pin ต้องเป็นตัวเลข"

        if action == "read":
            p = Pin(pin_num, Pin.IN)
            return f"📍 GPIO{pin_num} = {p.value()}"
        elif action == "write":
            if len(args) < 3:
                return "❌ ใช้: gpio write <pin> <0|1>"
            try:
                val = int(args[2])
            except ValueError:
                return "❌ value ต้องเป็น 0 หรือ 1"
            p = Pin(pin_num, Pin.OUT)
            p.value(val)
            return f"✅ GPIO{pin_num} = {val}"
        return "❌ action ต้องเป็น read หรือ write"

    @dispatcher.command("adc", "อ่านค่า ADC  |  ใช้: adc <pin>")
    def adc_cmd(*args):
        from machine import ADC, Pin
        if not args:
            return "❌ ใช้: adc <pin>  เช่น  adc 0"
        try:
            pin_num = int(args[0])
            adc = ADC(Pin(pin_num))
            adc.atten(ADC.ATTN_11DB)
            val = adc.read()
            voltage = val / 4095 * 3.3
            return f"📊 ADC{pin_num}: raw={val}  voltage={voltage:.2f}V"
        except Exception as e:
            return f"❌ อ่าน ADC ไม่ได้: {e}"

    repl = UARTRepl(dispatcher, uart_id=1, tx=21, rx=20, baudrate=115200)
    await repl.start()

    print("🔌 UART REPL พร้อมใช้งาน — GPIO21 TX, GPIO20 RX, 115200bps")
    while True:
        await asyncio.sleep(1)


# ============================================================
# ตัวอย่างที่ 4 — BLE REPL (Bluetooth)
# ============================================================

async def example_4_ble_repl():
    """
    🟡 ระดับกลาง — BLE REPL ผ่าน Bluetooth UART (Nordic NUS)

    วิธีเชื่อมต่อ:
        1. ดาวน์โหลด nRF Toolbox หรือ Serial Bluetooth Terminal บน Android/iOS
        2. Scan Bluetooth devices หา "ESP32-REPL"
        3. เชื่อมต่อ และเปิด UART plugin
        4. พิมพ์คำสั่งแล้วกด Send

    หมายเหตุ: response ยาวจะถูกแบ่งส่งเป็น packet 20 bytes ตาม BLE MTU
    """
    print("=== ตัวอย่างที่ 4: BLE REPL ===")

    dispatcher = CommandDispatcher(
        prompt="ble> ",
        welcome="ESP32 BLE REPL\nพิมพ์ help",
    )

    @dispatcher.command("blink", "กระพริบ LED  |  ใช้: blink <count> <ms>")
    def blink_cmd(*args):
        from machine import Pin
        import time
        count = int(args[0]) if args else 3
        ms = int(args[1]) if len(args) > 1 else 200
        led = Pin(2, Pin.OUT)
        for _ in range(count):
            led.on()
            time.sleep_ms(ms)
            led.off()
            time.sleep_ms(ms)
        return f"✅ กระพริบ {count} ครั้ง"

    @dispatcher.command("scan_wifi", "สแกน WiFi รอบข้าง")
    async def scan_wifi(*args):
        import network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        nets = wlan.scan()
        lines = [f"📡 พบ {len(nets)} เครือข่าย:"]
        for n in nets[:5]:  # แสดง 5 อันแรก (จำกัด BLE payload)
            ssid = n[0].decode() if isinstance(n[0], bytes) else n[0]
            rssi = n[3]
            lines.append(f"  {ssid} ({rssi}dBm)")
        return "\n".join(lines)

    repl = BLERepl(dispatcher, name="ESP32-REPL")
    await repl.start()

    print("📱 BLE REPL พร้อม — ค้นหา 'ESP32-REPL' ใน Bluetooth settings")
    while True:
        await asyncio.sleep(1)


# ============================================================
# ตัวอย่างที่ 5 — Multi-Transport (TCP + BLE พร้อมกัน)
# ============================================================

async def example_5_multi_transport():
    """
    🔴 มืออาชีพ — TCP REPL และ BLE REPL ทำงานพร้อมกันด้วย dispatcher เดียวกัน

    ใช้ CommandDispatcher ร่วมกัน → ลงทะเบียน command ครั้งเดียว
    ใช้ได้จาก WiFi (telnet) และ Bluetooth พร้อมกัน
    """
    print("=== ตัวอย่างที่ 5: Multi-Transport ===")

    # WiFi
    from wifi.wifimanager import WiFiManager
    wifi = WiFiManager()
    await wifi.connect("MySSID", "MyPassword")
    ip = wifi.get_ip()

    # Shared dispatcher
    dispatcher = CommandDispatcher(
        prompt="> ",
        welcome="ESP32 Multi-Transport REPL\nพิมพ์ help",
    )

    # ──── Commands ────

    @dispatcher.command("status", "แสดงสถานะระบบ")
    def status(*args):
        import gc
        return (
            f"📊 System Status\r\n"
            f"  WiFi: {ip}\r\n"
            f"  Free RAM: {gc.mem_free()} bytes\r\n"
            f"  BLE: {'connected' if ble_repl.is_connected else 'advertising'}"
        )

    @dispatcher.command("led", "เปิด/ปิด LED  |  ใช้: led <on|off>")
    def led(*args):
        from machine import Pin
        state = args[0].lower() if args else "on"
        Pin(2, Pin.OUT).value(1 if state == "on" else 0)
        return f"💡 LED {'เปิด' if state == 'on' else 'ปิด'}"

    @dispatcher.command("temp", "อ่านอุณหภูมิ (จำลอง)")
    def temp(*args):
        import random
        t = 20.0 + random.random() * 15
        return f"🌡 {t:.1f}°C"

    # ──── Transports ────

    # TCP REPL
    tcp_repl = TCPRepl(dispatcher, port=8266)
    await tcp_repl.start()

    # BLE REPL
    ble_repl = BLERepl(dispatcher, name="ESP32-REPL")
    await ble_repl.start()

    # WebREPL (เปิดด้วย — ใช้ browser เชื่อมต่อ)
    web_repl = WebREPL(password="esp32ok")
    web_repl.enable()

    print(f"✅ Multi-Transport REPL พร้อม:")
    print(f"   TCP: telnet {ip} 8266")
    print(f"   BLE: ค้นหา 'ESP32-REPL'")
    print(f"   WebREPL: {web_repl.get_url()}")

    # สร้าง background task ส่ง telemetry ทุก 30 วินาที
    async def telemetry_loop():
        import random
        while True:
            await asyncio.sleep(30)
            msg = f"📈 Auto: temp={20+random.random()*10:.1f}°C mem={__import__('gc').mem_free()}B\r\n"
            ble_repl.send(msg)

    asyncio.create_task(telemetry_loop())

    # keep running
    while True:
        await asyncio.sleep(10)


# ============================================================
# Run ตัวอย่าง
# ============================================================

if __name__ == "__main__":
    # เปลี่ยนเลขเพื่อรันตัวอย่างที่ต้องการ
    asyncio.run(example_1_basic_dispatcher())
