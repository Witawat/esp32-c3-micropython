---
title: "Ethernet"
cat: network
icon: 🔌
order: 8
desc: "Ethernet ผ่าน external PHY (LAN8720) แบบ RMII — DHCP/static IP, MAC และ async connect"
keywords: "ethernet, lan, rmii, lan8720, mdc, mdio, phy, dhcp, static ip, wired, network"
---

## ภาพรวมและแนวคิดการใช้งาน

`ethernet` เชื่อมต่อ ESP32 กับเน็ตผ่านสายแลนแทน WiFi โดยใช้ **external PHY chip** (เช่น LAN8720) ผ่าน interface RMII

> ⚠️ **ESP32-C3 ไม่รองรับ Ethernet แบบนี้** — โมดูลนี้ใช้ `network.LAN` (built-in EMAC) ซึ่ง **มีเฉพาะใน ESP32 (classic) เท่านั้น** ESP32-C3 ไม่มี EMAC peripheral และไม่มี GPIO ครบตามตารางข้างล่าง (C3 มีแค่ GPIO0–21) — ถ้าใช้กับ C3 ตัว constructor จะเตือน warning และ `connect()` จะคืน `False` (ไม่มี interface)

- **`EthernetManager`** — สร้าง `network.LAN`, เชื่อมต่อ (DHCP), ตั้ง static IP, อ่าน MAC/ifconfig, เวอร์ชัน async

แนวคิดหลัก: RMII ใช้ GPIO 8–10 ขา (MDC/MDIO + 4 สายข้อมูล + REF_CLK) ต้องมี 50MHz clock (จากคริสตัลบนโมดูล LAN8720 หรือจาก GPIO) เหมาะกับระบบที่ต้องการการเชื่อมต่อที่เสถียร/ไม่ต้องพึ่ง WiFi

## การติดตั้ง / import

```python
import sys
sys.path.append('/lib')

from ethernet.ethernet_manager import EthernetManager
```

## Constructor

`EthernetManager(mdc=23, mdio=18, phy_type="LAN8720", phy_addr=1, ref_clk="gpio17_out", power_pin=None, lan_id=0)`

| พารามิเตอร์ | ค่าเริ่มต้น | ความหมาย |
|---|---|---|
| `mdc` | `23` | GPIO ของ MDC (Management Data Clock) |
| `mdio` | `18` | GPIO ของ MDIO (Management Data I/O) |
| `phy_type` | `"LAN8720"` | `LAN8720/IP101/DP83848/RTL8201/KSZ8041` |
| `phy_addr` | `1` | ที่อยู่ PHY บน MDIO bus (ปกติ 0 หรือ 1) |
| `ref_clk` | `"gpio17_out"` | แหล่ง clock 50MHz: `gpio0_in`/`gpio0_out`/`gpio16_out`/`gpio17_out` |
| `power_pin` | `None` | GPIO ควบคุมไฟ PHY (เปิดให้อัตโนมัติตอน init) |
| `lan_id` | `0` | LAN interface ID |

ค่าคงที่: `PHY_LAN8720=0 … PHY_KSZ8041=4`, `CLOCK_GPIO0_IN/OUT`, `CLOCK_GPIO16_OUT`, `CLOCK_GPIO17_OUT`

## ตาราง API

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ต้องใช้รวมกับ |
|---|---|---|---|---|
| `connect(timeout_ms)` | เชื่อมต่อแบบ DHCP | `timeout_ms=15000` | `bool` | ก่อนใช้เน็ต |
| `disconnect()` | ตัดการเชื่อมต่อ | — | `bool` | เรียกตอนจบ |
| `ifconfig()` | อ่าน config เน็ต | — | `tuple (ip, netmask, gateway, dns)` | หลัง `connect()` |
| `is_connected()` | เช็คสถานะ | — | `bool` | ใช้ monitor |
| `set_static(ip, netmask, gateway, dns)` | ตั้ง IP คงที่ | `dns="8.8.8.8"` | — | ก่อน/หลัง connect ได้ |
| `mac_address()` | อ่าน MAC | — | `str` (เช่น `"AA:BB:.."`) | — |
| `async_connect(timeout_ms)` | เวอร์ชัน async | `timeout_ms=15000` | `bool` | ใช้ใน event loop |
| `deinit()` | ปิดและคืนทรัพยากร | — | — | เรียกตอนจบ |
| `ip_address` / `netmask` / `gateway` / `dns` | properties อ่านค่า | — | `str` | หลัง `connect()` |

## ตัวอย่างการใช้งาน

### 🟢 พื้นฐาน — เชื่อมต่อแบบ DHCP

```python
import sys
sys.path.append('/lib')

from ethernet.ethernet_manager import EthernetManager

eth = EthernetManager(mdc=23, mdio=18)

if eth.connect(timeout_ms=10000):
    print(f"🌐 เชื่อมต่อแล้ว IP: {eth.ip_address}")
    print(f"MAC: {eth.mac_address()}")
    print(f"DNS: {eth.dns}")
else:
    print("เชื่อมต่อไม่สำเร็จ")

eth.disconnect()
```

### 🟡 ใช้งานจริง — static IP + เช็คสถานะ

```python
import sys
sys.path.append('/lib')

import time
from ethernet.ethernet_manager import EthernetManager

eth = EthernetManager()
eth.set_static("192.168.1.100", "255.255.255.0", "192.168.1.1", dns="8.8.8.8")

if eth.connect():
    while True:
        print("🟢 ออนไลน์" if eth.is_connected() else "🔴 หลุด")
        time.sleep(5)
```

### 🔴 ขั้นสูง — async รันร่วมกับงานอื่น

```python
import sys
sys.path.append('/lib')

import asyncio
from ethernet.ethernet_manager import EthernetManager

async def main():
    eth = EthernetManager()
    if await eth.async_connect():
        print(f"IP: {eth.ip_address}")
        # รันงาน HTTP/MQTT ต่อได้เลย
    eth.deinit()

asyncio.run(main())
```

## การต่อวงจร (ESP32 + LAN8720)

> ตารางนี้เป็นพินของ **ESP32 (classic)** ที่มี EMAC — ใช้กับ C3 ไม่ได้ (GPIO22–27 ไม่มีบน C3)

```text
ESP32-C3          LAN8720
─────────         ───────
GPIO23 (MDC) ──→  MDC
GPIO18 (MDIO)──→  MDIO
GPIO19 (TXD0)──→  TXD0
GPIO21 (TX_EN)──→ TX_EN
GPIO22 (TXD1)──→  TXD1
GPIO25 (RXD0) ←── RXD0
GPIO26 (RXD1) ←── RXD1
GPIO27 (CRS)  ←── CRS_DV
GPIO17 (REF)  ──  50MHz clock out
3.3V          ──→ VCC
GND           ──── GND
```

| ข้อ | รายละเอียด |
|---|---|
| PHY | ต้องเป็นโมดูล LAN8720 (หรือตาม `phy_type`) |
| Clock | บอร์ด LAN8720 ส่วนใหญ่มีคริสตัล 50MHz ในตัว — ถ้าไม่มีต้องใช้ `ref_clk` จาก GPIO |
| พิน | ใช้ 8–10 GPIO — ต้องดูว่าไม่ชนพินที่ใช้กับอย่างอื่น |
| ไฟ | PHY กิน ~100–300mW |

## ข้อควรระวัง

- **ESP32-C3 ใช้โมดูลนี้ไม่ได้** — C3 ไม่มี EMAC/`network.LAN` และไม่มี GPIO22–27 ใช้ได้เฉพาะ ESP32 (classic) ที่มี EMAC (พิน GPIO18–27)
- ถ้า `network.LAN` API ต่างระหว่าง MicroPython port การสร้าง LAN ใน constructor อาจล้มเหลวแต่ไม่ crash (เตือนเป็น warning)
- พิน RMII จำนวนมาก — วางแผน GPIO ให้ดี อย่าชนกับ SPI/I2C ที่ใช้อยู่
- `ref_clk="gpio17_out"` เป็นค่า default — ถ้าบอร์ดมีคริสตัลในตัว อาจต้องลองค่า clock mode อื่น

## ใช้ร่วมกับ

- `mqtt` / `http` / `websocket` / `telegram` — ใช้เน็ตต่อจาก Ethernet เหมือน WiFi
- `wifi.wifimanager.WiFiManager` — ทำ failover: ใช้ Ethernet ก่อน ถ้าพลาดค่อยสลับ WiFi
- `storage.config_mgr.JsonConfigManager` — เก็บ static IP/config (อัตโนมัติ)
