"""
WiFi Manager Module สำหรับ ESP32-C3
จัดการการเชื่อมต่อ WiFi แบบ STA Mode
เก็บค่า configuration ใน wifi_config.json

วิธีใช้งาน:
    from wifimanager import WiFiManager
    
    # เชื่อมต่อ WiFi
    wifi = WiFiManager()
    await wifi.connect()
    
    # หรือระบุ config file path เอง
    wifi = WiFiManager(config_file="my_wifi_config.json")
    await wifi.connect()
"""

import asyncio
import json
import network
import os
from machine import Pin

try:
    from storage.config_mgr import JsonConfigManager
except ImportError:
    JsonConfigManager = None

# Import HTML template จากไฟล์แยก
try:
    from wifi.wifi_portal_html import PORTAL_HTML, ERROR_404_HTML
except ImportError:
    # Fallback หากไม่สามารถ import ได้
    PORTAL_HTML = "<html><body><h1>WiFi Portal</h1></body></html>"
    ERROR_404_HTML = "<html><body><h1>404</h1></body></html>"


class WiFiManager:
    """
    จัดการการเชื่อมต่อ WiFi แบบ STA Mode
    เก็บค่า configuration ในไฟล์ JSON
    """
    
    def __init__(self, config_file="wifi_config.json"):
        """
        สร้าง instance ของ WiFiManager
        
        Args:
            config_file (str): ชื่อไฟล์ configuration (default: "wifi_config.json")
        """
        self.config_file = config_file
        self.wlan = network.WLAN(network.STA_IF)
        self.connected = False
        self.config = {}
        self._config_mgr = JsonConfigManager(config_file) if JsonConfigManager else None
        
    def load_config(self):
        """
        โหลด configuration จากไฟล์ JSON
        
        Returns:
            dict: configuration ที่โหลดมา หรือ {} หากไม่พบไฟล์
        """
        if self._config_mgr:
            self.config = self._config_mgr.load(default={})
            if self.config:
                print(f"📄 โหลด config จาก {self.config_file} สำเร็จ")
            else:
                print(f"⚠️ ไม่พบไฟล์ {self.config_file}")
            return self.config

        try:
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
                print(f"📄 โหลด config จาก {self.config_file} สำเร็จ")
                return self.config
        except OSError:
            print(f"⚠️ ไม่พบไฟล์ {self.config_file}")
            self.config = {}
            return self.config
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการโหลด config: {e}")
            self.config = {}
            return self.config
    
    def save_config(self, ssid=None, password=None):
        """
        บันทึก configuration ลงไฟล์ JSON
        
        Args:
            ssid (str): ชื่อ WiFi ที่จะบันทึก (ถ้า None จะใช้ค่าที่มีอยู่)
            password (str): รหัสผ่าน WiFi ที่จะบันทึก (ถ้า None จะใช้ค่าที่มีอยู่)
        
        Returns:
            bool: True หากบันทึกสำเร็จ, False หากเกิดข้อผิดพลาด
        """
        if ssid is not None:
            self.config["ssid"] = ssid
        if password is not None:
            self.config["password"] = password
        
        # เพิ่มค่า default หากยังไม่มี
        if "auto_connect" not in self.config:
            self.config["auto_connect"] = True
        if "timeout" not in self.config:
            self.config["timeout"] = 15
        if "reconnect" not in self.config:
            self.config["reconnect"] = True
        if "reconnect_interval" not in self.config:
            self.config["reconnect_interval"] = 30
        
        if self._config_mgr:
            ok = self._config_mgr.save(self.config)
            if ok:
                print(f"💾 บันทึก config ลง {self.config_file} สำเร็จ")
            return ok

        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f)
                print(f"💾 บันทึก config ลง {self.config_file} สำเร็จ")
                return True
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการบันทึก config: {e}")
            return False
    
    def update_config(self, new_config):
        """
        อัปเดต configuration แบบ dictionary
        
        Args:
            new_config (dict): configuration ใหม่ที่จะอัปเดต
        
        Returns:
            bool: True หากอัปเดตสำเร็จ
        """
        self.config.update(new_config)
        return self.save_config()
    
    def get_config(self):
        """
        ดึง configuration ปัจจุบัน
        
        Returns:
            dict: configuration ปัจจุบัน
        """
        return self.config.copy()
    
    def is_connected(self):
        """
        ตรวจสอบว่าเชื่อมต่อ WiFi หรือไม่
        
        Returns:
            bool: True หากเชื่อมต่ออยู่, False หากไม่เชื่อมต่อ
        """
        return self.wlan.isconnected()
    
    def get_ip(self):
        """
        ดึง IP address ปัจจุบัน
        
        Returns:
            str: IP address หรือ None หากไม่เชื่อมต่อ
        """
        if self.wlan.isconnected():
            return self.wlan.ifconfig()[0]
        return None
    
    def get_connection_info(self):
        """
        ดึงข้อมูลการเชื่อมต่อทั้งหมด
        
        Returns:
            dict: ข้อมูลการเชื่อมต่อ
        """
        if self.wlan.isconnected():
            ip, subnet, gateway, dns = self.wlan.ifconfig()
            return {
                "connected": True,
                "ip": ip,
                "subnet": subnet,
                "gateway": gateway,
                "dns": dns,
                "mac": ":".join(["{:02x}".format(b) for b in self.wlan.config("mac")]),
                "ssid": self.config.get("ssid", "unknown")
            }
        return {
            "connected": False,
            "ssid": self.config.get("ssid", "unknown")
        }
    
    async def scan_networks(self):
        """
        สแกน WiFi networks ที่มีอยู่
        
        Returns:
            list: รายการ WiFi networks ที่พบ
        """
        print("📡 กำลังสแกน WiFi networks...")
        
        # ต้องเปิด WiFi ก่อน
        self.wlan.active(True)
        
        # สแกน networks
        networks = self.wlan.scan()
        
        print(f"✅ พบ {len(networks)} networks:")
        result = []
        for net in networks:
            ssid = net[0].decode("utf-8")
            signal_strength = net[3]
            auth_mode = net[4]
            channel = net[2]
            
            info = {
                "ssid": ssid,
                "signal": signal_strength,
                "channel": channel,
                "secure": auth_mode != 0
            }
            result.append(info)
            print(f"   📶 {ssid} (Signal: {signal_strength} dBm, Channel: {channel})")
        
        return result
    
    async def connect(self, ssid=None, password=None, timeout=None):
        """
        เชื่อมต่อ WiFi
        
        Args:
            ssid (str): ชื่อ WiFi (ถ้า None จะใช้จาก config)
            password (str): รหัสผ่าน WiFi (ถ้า None จะใช้จาก config)
            timeout (int): เวลาหนีก่อน timeout เป็นวินาที (ถ้า None จะใช้จาก config)
        
        Returns:
            bool: True หากเชื่อมต่อสำเร็จ, False หากไม่สำเร็จ
        """
        # โหลด config ก่อน
        self.load_config()
        
        # ใช้ค่าจาก parameter หรือ config
        target_ssid = ssid or self.config.get("ssid")
        target_password = password or self.config.get("password", "")
        target_timeout = timeout or self.config.get("timeout", 15)
        
        if not target_ssid:
            print("❌ ไม่พบ SSID ใน config หรือ parameter")
            return False
        
        # ตรวจสอบว่าเชื่อมต่ออยู่แล้วหรือไม่
        if self.wlan.isconnected():
            print(f"✅ WiFi เชื่อมต่ออยู่แล้ว: {target_ssid}")
            self.connected = True
            return True
        
        print(f"📡 กำลังเชื่อมต่อ WiFi: {target_ssid}")
        
        # เปิด WiFi
        self.wlan.active(True)
        
        # ตั้งค่า hostname (optional)
        if "hostname" in self.config:
            self.wlan.config(dhcp_hostname=self.config["hostname"])
        
        # เชื่อมต่อ
        self.wlan.connect(target_ssid, target_password)
        
        # รอจนกว่าจะเชื่อมต่อ หรือ timeout
        count = 0
        while count < target_timeout:
            if self.wlan.isconnected():
                self.connected = True
                ip = self.wlan.ifconfig()[0]
                print(f"✅ เชื่อมต่อ WiFi สำเร็จ!")
                print(f"   SSID: {target_ssid}")
                print(f"   IP: {ip}")
                
                # บันทึก config หากมีการเปลี่ยนแปลง
                if target_ssid != self.config.get("ssid"):
                    self.save_config(ssid=target_ssid, password=target_password)
                
                return True
            
            await asyncio.sleep(1)
            count += 1
            print(f"⏳ รอเชื่อมต่อ... ({count}/{target_timeout} วินาที)")
        
        # หาก timeout
        print(f"❌ ไม่สามารถเชื่อมต่อ WiFi ได้ภายใน {target_timeout} วินาที")
        self.connected = False
        return False
    
    async def disconnect(self):
        """
        ยกเลิกการเชื่อมต่อ WiFi
        
        Returns:
            bool: True หากยกเลิกสำเร็จ
        """
        if self.wlan.isconnected():
            self.wlan.disconnect()
            self.connected = False
            print("👋 ยกเลิกการเชื่อมต่อ WiFi แล้ว")
            return True
        return False
    
    async def reconnect(self):
        """
        เชื่อมต่อ WiFi ใหม่
        
        Returns:
            bool: True หากเชื่อมต่อสำเร็จ
        """
        await self.disconnect()
        await asyncio.sleep(1)
        return await self.connect()
    
    async def keep_alive(self, check_interval=None):
        """
        ตรวจสอบการเชื่อมต่อ WiFi เป็นระยะ และเชื่อมต่อใหม่หากหลุด
        
        Args:
            check_interval (int): ช่วงเวลาในการตรวจสอบ เป็นวินาที
        
        Returns:
            None: ทำงานตลอดไปจนกว่าจะถูกหยุด
        """
        interval = check_interval or self.config.get("reconnect_interval", 30)
        self._keep_alive_running = True
        
        print(f"🔄 เริ่ม keep-alive mode (ตรวจสอบทุก {interval} วินาที)")
        
        while self._keep_alive_running:
            if not self.wlan.isconnected():
                print("⚠️ WiFi ขาด! กำลังเชื่อมต่อใหม่...")
                self.connected = False
                
                success = await self.connect()
                if not success:
                    print("⚠️ เชื่อมต่อใหม่ไม่สำเร็จ จะลองใหม่ในรอบถัดไป")
            
            await asyncio.sleep(interval)
    
    def stop_keep_alive(self):
        """
        หยุด keep-alive mode
        """
        self._keep_alive_running = False
        print("⏹️ หยุด keep-alive mode")
    
    def set_auto_connect(self, enabled=True):
        """
        เปิด/ปิด auto connect
        
        Args:
            enabled (bool): True เพื่อเปิด auto connect
        """
        self.config["auto_connect"] = enabled
        self.save_config()
    
    async def connect_auto(self):
        """
        เชื่อมต่อ WiFi อัตโนมัติตามค่า config
        
        Returns:
            bool: True หากเชื่อมต่อสำเร็จ, False หากไม่สำเร็จหรือไม่ได้เปิด auto connect
        """
        self.load_config()
        
        if not self.config.get("auto_connect", True):
            print("ℹ️ Auto connect ปิดอยู่")
            return False
        
        return await self.connect()
    
    def get_status(self):
        """
        ดึงสถานะ WiFi แบบ string
        
        Returns:
            str: สถานะ WiFi
        """
        if self.wlan.isconnected():
            return f"✅ Connected - {self.wlan.ifconfig()[0]}"
        else:
            return "❌ Disconnected"
    
    def __str__(self):
        """
        String representation
        
        Returns:
            str: ข้อมูล WiFi
        """
        info = self.get_connection_info()
        return f"WiFiManager(ssid={info['ssid']}, connected={info['connected']})"


# ========== ตัวอย่างการใช้งาน ==========

async def example_basic():
    """ตัวอย่างพื้นฐาน - เชื่อมต่อ WiFi"""
    wifi = WiFiManager()
    
    # บันทึก config ครั้งแรก
    wifi.save_config(
        ssid="your_wifi_ssid",
        password="your_wifi_password"
    )
    
    # เชื่อมต่อ
    success = await wifi.connect()
    
    if success:
        print(f"IP Address: {wifi.get_ip()}")
        print(wifi.get_connection_info())


async def example_with_scan():
    """ตัวอย่าง - สแกนและเชื่อมต่อ"""
    wifi = WiFiManager()
    
    # สแกน networks
    networks = await wifi.scan_networks()
    
    # เลือก network ที่ต้องการ
    target_ssid = "your_wifi_ssid"
    target_password = "your_wifi_password"
    
    # เชื่อมต่อ
    await wifi.connect(ssid=target_ssid, password=target_password)


async def example_keep_alive():
    """ตัวอย่าง - keep-alive mode"""
    wifi = WiFiManager()
    
    # บันทึก config
    wifi.save_config(
        ssid="your_wifi_ssid",
        password="your_wifi_password",
        reconnect_interval=60  # ตรวจสอบทุก 60 วินาที
    )
    
    # เชื่อมต่อ
    await wifi.connect()
    
    # ทำงานใน keep-alive mode
    try:
        await wifi.keep_alive()
    except KeyboardInterrupt:
        wifi.stop_keep_alive()


async def example_multiple():
    """ตัวอย่าง - จัดการหลาย config files"""
    
    # Config สำหรับที่บ้าน
    home_wifi = WiFiManager(config_file="home_wifi.json")
    home_wifi.save_config(
        ssid="home_wifi",
        password="home_password"
    )
    
    # Config ที่ทำงาน
    work_wifi = WiFiManager(config_file="work_wifi.json")
    work_wifi.save_config(
        ssid="office_wifi",
        password="office_password"
    )
    
    # ใช้งาน
    await home_wifi.connect()
    print(f"Home IP: {home_wifi.get_ip()}")


# ========== WiFi Portal Web Server ==========
class WiFiPortal:
    """
    WiFi Configuration Portal
    สร้าง Web Server สำหรับตั้งค่า WiFi ผ่านหน้าเว็บ
    """
    
    def __init__(self, config_file="wifi_config.json"):
        """
        สร้าง WiFi Portal instance
        
        Args:
            config_file (str): ชื่อไฟล์ configuration
        """
        self.wifi = WiFiManager(config_file=config_file)
        self.server = None
        self._running = False
        
    async def start_ap_mode(self, ssid="ESP32-Setup", password="12345678"):
        """
        เริ่ม Access Point Mode
        
        Args:
            ssid (str): ชื่อ AP
            password (str): รหัสผ่าน AP (อย่างน้อย 8 ตัว)
        
        Returns:
            bool: True หากสำเร็จ
        """
        try:
            ap = network.WLAN(network.AP_IF)
            ap.config(essid=ssid, password=password, authmode=network.AUTH_WPA_WPA2_PSK)
            ap.active(True)
            
            # รอให้ AP เปิดสำเร็จ
            count = 0
            while not ap.active() and count < 10:
                await asyncio.sleep(0.5)
                count += 1
            
            if ap.active():
                ip = ap.ifconfig()[0]
                print(f"✅ AP Mode เปิดสำเร็จ!")
                print(f"   SSID: {ssid}")
                print(f"   Password: {password}")
                print(f"   IP: {ip}")
                print(f"\n📱 เปิดเว็บเบราว์เซอร์แล้วไปที่: http://{ip}")
                return True
            else:
                print("❌ ไม่สามารถเปิด AP Mode ได้")
                return False
                
        except Exception as e:
            print(f"❌ ข้อผิดพลาด: {e}")
            return False
    
    def _create_server(self):
        """สร้าง HTTP Server"""
        import socket
        
        addr = socket.getaddrinfo('0.0.0.0', 80, 0, socket.SOCK_STREAM)[0][-1]
        self.server = socket.socket()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(addr)
        self.server.listen(5)
        self.server.setblocking(False)
        
        print(f"🌐 HTTP Server เริ่มทำงานที่ port 80")
    
    async def _handle_client(self, client):
        """จัดการ client request"""
        try:
            # อ่าน request
            request = b""
            while True:
                await asyncio.sleep_ms(10)
                try:
                    chunk = client.recv(4096)
                    if chunk:
                        request += chunk
                        if b"\r\n\r\n" in request:
                            break
                    else:
                        break
                except:
                    break
            
            if not request:
                client.close()
                return
            
            # แปลง request
            request_str = request.decode("utf-8", errors="ignore")
            lines = request_str.split("\r\n")
            
            if not lines:
                client.close()
                return
            
            # ดึง method และ path
            request_line = lines[0].split(" ")
            if len(request_line) < 2:
                client.close()
                return
            
            method = request_line[0]
            path = request_line[1]
            
            # จัดการ request
            if path == "/" or path == "/index.html":
                await self._serve_html(client)
            elif path == "/api/status":
                await self._api_status(client)
            elif path == "/api/scan":
                await self._api_scan(client)
            elif path == "/api/save" and method == "POST":
                await self._api_save(client, request_str)
            elif path == "/api/test":
                await self._api_test(client)
            else:
                await self._serve_404(client)
            
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการจัดการ client: {e}")
            try:
                client.close()
            except:
                pass
        
        client.close()
    
    async def _serve_html(self, client):
        """ส่ง HTML page"""
        try:
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nConnection: close\r\n\r\n{PORTAL_HTML}"
            client.send(response.encode("utf-8"))
        except Exception as e:
            print(f"❌ ไม่สามารถส่ง HTML: {e}")
    
    async def _serve_404(self, client):
        """ส่ง 404 page"""
        response = f"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n{ERROR_404_HTML}"
        client.send(response.encode("utf-8"))
    
    async def _api_status(self, client):
        """ส่งสถานะ WiFi"""
        import json
        
        status = {
            "connected": self.wifi.is_connected(),
            "ip": self.wifi.get_ip(),
            "ssid": self.wifi.config.get("ssid", "")
        }
        
        import json
        response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n{json.dumps(status)}"
        client.send(response.encode("utf-8"))
    
    async def _api_scan(self, client):
        """สแกน WiFi networks"""
        import json
        
        try:
            self.wifi.wlan.active(True)
            networks = self.wifi.wlan.scan()
            
            result = []
            for net in networks:
                result.append({
                    "ssid": net[0].decode("utf-8"),
                    "signal": net[3],
                    "channel": net[2],
                    "secure": net[4] != 0
                })
            
            # เรียงตาม signal strength
            result.sort(key=lambda x: x["signal"], reverse=True)
            
            response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n{json.dumps(result)}"
            client.send(response.encode("utf-8"))
        except Exception as e:
            response = f"HTTP/1.1 500 Error\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n{{\"error\": \"{str(e)}\"}}"
            client.send(response.encode("utf-8"))
    
    async def _api_save(self, client, request_str):
        """บันทึกการตั้งค่า WiFi"""
        import json
        
        try:
            # ดึง JSON body
            body_start = request_str.find("\r\n\r\n")
            if body_start == -1:
                raise Exception("Invalid request")
            
            body = request_str[body_start + 4:]
            data = json.loads(body)
            
            # บันทึก config
            self.wifi.config.update(data)
            self.wifi.save_config(
                ssid=data.get("ssid"),
                password=data.get("password")
            )
            
            # อัปเดต options
            if "auto_connect" in data:
                self.wifi.config["auto_connect"] = data["auto_connect"]
            if "reconnect" in data:
                self.wifi.config["reconnect"] = data["reconnect"]
            if "timeout" in data:
                self.wifi.config["timeout"] = data["timeout"]
            if "reconnect_interval" in data:
                self.wifi.config["reconnect_interval"] = data["reconnect_interval"]
            
            # เชื่อมต่อ WiFi
            success = await self.wifi.connect()
            
            result = {
                "success": success,
                "connected": self.wifi.is_connected(),
                "ip": self.wifi.get_ip()
            }
            
            response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n{json.dumps(result)}"
            client.send(response.encode("utf-8"))
        except Exception as e:
            import json
            result = {"success": False, "error": str(e)}
            response = f"HTTP/1.1 500 Error\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n{json.dumps(result)}"
            client.send(response.encode("utf-8"))
    
    async def _api_test(self, client):
        """ทดสอบการเชื่อมต่อ"""
        import json
        
        success = await self.wifi.connect()
        
        result = {
            "connected": self.wifi.is_connected(),
            "ip": self.wifi.get_ip()
        }
        
        response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n{json.dumps(result)}"
        client.send(response.encode("utf-8"))
    
    async def start_portal(self, ap_ssid="ESP32-Setup", ap_password="12345678"):
        """
        เริ่ม WiFi Portal
        
        Args:
            ap_ssid (str): ชื่อ AP
            ap_password (str): รหัสผ่าน AP
        
        Returns:
            bool: True หากสำเร็จ
        """
        print("=" * 50)
        print("🚀 เริ่ม WiFi Configuration Portal")
        print("=" * 50)
        
        # เปิด AP Mode
        if not await self.start_ap_mode(ap_ssid, ap_password):
            return False
        
        # สร้าง HTTP Server
        self._create_server()
        self._running = True
        
        print("\n✅ Portal พร้อมแล้ว!")
        print("💡 วิธีใช้งาน:")
        print(f"   1. เชื่อมต่อ WiFi: {ap_ssid}")
        print(f"   2. รหัสผ่าน: {ap_password}")
        print(f"   3. เปิดเบราว์เซอร์: http://192.168.4.1")
        print(f"   4. ตั้งค่า WiFi และกดบันทึก")
        
        # จัดการ clients
        try:
            while self._running:
                await asyncio.sleep_ms(100)
                
                try:
                    # รับ connection
                    client, addr = self.server.accept()  # type: ignore[union-attr]
                    client.setblocking(False)
                    
                    # จัดการ client
                    asyncio.create_task(self._handle_client(client))
                except:
                    # ไม่มี client
                    pass
        except KeyboardInterrupt:
            print("\n⏹️ หยุด Portal")
            await self.stop()
        
        return True
    
    async def stop(self):
        """หยุด Portal"""
        self._running = False
        
        if self.server:
            self.server.close()
            print("⏹️ HTTP Server หยุดแล้ว")
        
        # ปิด AP
        try:
            ap = network.WLAN(network.AP_IF)
            ap.active(False)
            print("⏹️ AP Mode ปิดแล้ว")
        except:
            pass
    
    def __str__(self):
        return f"WiFiPortal(ap_active={self._running})"


# ========== เริ่มต้นโปรแกรม ==========
if __name__ == "__main__":
    # เลือกตัวอย่างที่ต้องการรัน
    
    asyncio.run(example_basic())
    # asyncio.run(example_with_scan())
    # asyncio.run(example_keep_alive())
    # asyncio.run(example_multiple())
