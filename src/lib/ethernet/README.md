# Ethernet Manager — Wired Network

> **Interface**: `network.LAN` (RMII external PHY)  
> **รองรับ**: ESP32 (ทุกรุ่นที่มี RMII interface)  

> **⚠️ ESP32-C3 ไม่มี built-in Ethernet MAC** — ต้องใช้ external PHY chip (LAN8720, IP101 ฯลฯ) ผ่าน RMII interface (ใช้ 8-10 GPIO pins)

---

## การเชื่อมต่อ (ESP32-C3 + LAN8720)

```
ESP32-C3          LAN8720 Module
─────────         ───────────────
GPIO23 (MDC)  ──→ MDC
GPIO18 (MDIO) ──→ MDIO
GPIO19 (TXD0) ──→ TXD0
GPIO21 (TX_EN) ──→ TX_EN
GPIO22 (TXD1) ──→ TXD1
GPIO25 (RXD0) ←── RXD0
GPIO26 (RXD1) ←── RXD1
GPIO27 (CRS)  ←── CRS_DV
GPIO17        ──→ 50MHz clock out (ขึ้นอยู่กับ config)
3.3V          ──→ VCC
GND           ─── GND

RJ45 (LAN8720) → Ethernet cable → Router/Switch
```

---

## 🟢 Basic Usage

```python
from ethernet import EthernetManager

# เริ่มต้น Ethernet
eth = EthernetManager(mdc=23, mdio=18, phy_type='LAN8720')

# เชื่อมต่อ (DHCP)
if eth.connect():
    print(f"IP: {eth.ip_address}")
    print(f"MAC: {eth.mac_address()}")

# ตรวจสอบว่ายังเชื่อมต่ออยู่
if eth.is_connected():
    print("✅ Connected")

# ยกเลิกการเชื่อมต่อ
eth.disconnect()
```

---

## 🟡 Intermediate Usage

```python
from ethernet import EthernetManager

# Static IP
eth = EthernetManager(mdc=23, mdio=18)
eth.set_static(
    ip='192.168.1.100',
    netmask='255.255.255.0',
    gateway='192.168.1.1',
    dns='8.8.8.8'
)

# อ่าน network info
ip, netmask, gw, dns = eth.ifconfig()
print(f"IP: {ip}")
print(f"Gateway: {gw}")

# Async connect
import asyncio

async def main():
    eth = EthernetManager(mdc=23, mdio=18)
    if await eth.async_connect():
        print(f"Connected: {eth.ip_address}")

asyncio.run(main())
```

---

## 🔴 Advanced Usage

```python
from ethernet import EthernetManager
from wifi import WiFiManager
import asyncio

# ── Ethernet + WiFi failover ──
class NetworkFailover:
    """Fallback ระหว่าง Ethernet และ WiFi"""
    
    def __init__(self):
        self.eth = EthernetManager(mdc=23, mdio=18)
        self.wifi = WiFiManager()
        self._active_iface = None
    
    async def connect(self):
        """ลอง Ethernet ก่อน ถ้าไม่สำเร็จใช้ WiFi"""
        if self.eth.connect():
            self._active_iface = self.eth
            print(f"🌐 Using Ethernet: {self.eth.ip_address}")
        else:
            print("⚠️ Ethernet failed, trying WiFi...")
            await self.wifi.connect()
            self._active_iface = self.wifi
            print(f"📡 Using WiFi")
        
        return self.is_connected()
    
    def is_connected(self):
        if self._active_iface:
            return self._active_iface.is_connected()
        return False

# ── ใช้ HTTP ผ่าน Ethernet ──
# เมื่อเชื่อมต่อ Ethernet แล้ว, HTTPClient/MQTTManager จะทำงานผ่าน
# default route โดยอัตโนมัติ — ไม่ต้องแก้โค้ดเดิมเลย!
from http import HTTPClient

async def main():
    net = NetworkFailover()
    if await net.connect():
        http = HTTPClient()
        resp = http.get('http://example.com/api/data')
        print(resp.text)

asyncio.run(main())
```

---

## API Reference

### `EthernetManager`

| Method | Description |
|---|---|
| `__init__(mdc, mdio, phy_type, phy_addr, ref_clk, power_pin)` | สร้าง Ethernet instance |
| `connect(timeout_ms)` | เชื่อมต่อ (DHCP) |
| `disconnect()` | ยกเลิกการเชื่อมต่อ |
| `ifconfig()` | อ่าน (ip, netmask, gw, dns) |
| `is_connected()` | Check connection |
| `set_static(ip, nm, gw, dns)` | Static IP |
| `mac_address()` | MAC address |
| `async_connect(timeout_ms)` | Async connect |
| `deinit()` | Cleanup |

---

## ESP32-C3 Specific

| Item | Value |
|---|---|
| Built-in MAC | ❌ ไม่มี |
| External PHY | ✅ ผ่าน RMII |
| PHY chips | LAN8720, IP101, DP83848, RTL8201, KSZ8041 |
| GPIO usage | 8-10 pins (MDC, MDIO, TXD0/1, TX_EN, RXD0/1, CRS, REF_CLK) |
| Clock source | GPIO0/16/17 output 50MHz หรือ external oscillator |
| Speed | 10/100 Mbps |
| Power | PHY chip ใช้ ~100-300mW |
