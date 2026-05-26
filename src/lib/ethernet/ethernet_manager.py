"""
Ethernet Manager สำหรับ ESP32-C3
Interface: network.LAN (RMII external PHY)
รองรับ: ESP32 (ทุกรุ่นที่มี RMII interface)

รองรับ PHY chips:
- LAN8720 (common on dev boards)
- IP101
- DP83848
- RTL8201
- KSZ8041

ข้อจำกัด ESP32-C3:
- ไม่มี built-in Ethernet MAC → ต้องใช้ external PHY chip ผ่าน RMII
- ใช้ 8-10 GPIO pins สำหรับ RMII interface
- ต้องการ clock source (crystal หรือ GPIO output)

การเชื่อมต่อ (ESP32-C3 + LAN8720):
    ESP32-C3          LAN8720
    ─────────         ───────
    GPIO23 (MDC) ──→  MDC
    GPIO18 (MDIO) ──→ MDIO
    GPIO19 (TXD0) ──→ TXD0
    GPIO21 (TX_EN) ──→ TX_EN
    GPIO22 (TXD1) ──→ TXD1
    GPIO25 (RXD0) ←── RXD0
    GPIO26 (RXD1) ←── RXD1
    GPIO27 (CRS)  ←── CRS_DV
    GPIO0  (REF)  ──  50MHz clock (ขึ้นอยู่กับ config)
    3.3V          ──→ VCC
    GND           ─── GND
"""

import asyncio
import network

try:
    from machine import Pin
    HAS_MACHINE = True
except ImportError:
    HAS_MACHINE = False

# Optional: config persistence
try:
    from storage.config_mgr import JsonConfigManager
except ImportError:
    JsonConfigManager = None


class EthernetManager:
    """
    Ethernet Manager — abstraction layer on top of network.LAN

    รองรับ external PHY chips ผ่าน RMII interface

    ตัวอย่าง:
        eth = EthernetManager(mdc=23, mdio=18)
        eth.connect()
        print(eth.ip_address)
        eth.disconnect()

    หมายเหตุ:
        - ESP32-C3 ต้องใช้ external PHY chip (ไม่มี built-in MAC)
        - RMII ใช้ 8-10 GPIO pins
        - ต้องการ 50MHz reference clock
    """

    # PHY type constants
    PHY_LAN8720 = 0
    PHY_IP101 = 1
    PHY_DP83848 = 2
    PHY_RTL8201 = 3
    PHY_KSZ8041 = 4

    _PHY_MAP = {
        'LAN8720': PHY_LAN8720,
        'IP101': PHY_IP101,
        'DP83848': PHY_DP83848,
        'RTL8201': PHY_RTL8201,
        'KSZ8041': PHY_KSZ8041,
    }

    # Clock modes
    CLOCK_GPIO0_IN = 0     # External 50MHz on GPIO0
    CLOCK_GPIO0_OUT = 1    # Internal 50MHz on GPIO0
    CLOCK_GPIO16_OUT = 2   # Internal 50MHz on GPIO16
    CLOCK_GPIO17_OUT = 3   # Internal 50MHz on GPIO17

    _CLOCK_MAP = {
        'gpio0_in': CLOCK_GPIO0_IN,
        'gpio0_out': CLOCK_GPIO0_OUT,
        'gpio16_out': CLOCK_GPIO16_OUT,
        'gpio17_out': CLOCK_GPIO17_OUT,
    }

    def __init__(self, mdc: int = 23, mdio: int = 18,
                 phy_type: str = 'LAN8720',
                 phy_addr: int = 1,
                 ref_clk: str = 'gpio17_out',
                 power_pin: int = None,
                 lan_id: int = 0):
        """
        :param mdc: GPIO pin สำหรับ Management Data Clock
        :param mdio: GPIO pin สำหรับ Management Data I/O
        :param phy_type: PHY chip type ('LAN8720', 'IP101', 'DP83848', 'RTL8201', 'KSZ8041')
        :param phy_addr: PHY address บน MDIO bus (ปกติ 0 หรือ 1)
        :param ref_clk: reference clock source ('gpio0_in', 'gpio0_out', 'gpio16_out', 'gpio17_out')
        :param power_pin: GPIO pin สำหรับควบคุม power ของ PHY (None = ไม่ใช้)
        :param lan_id: LAN interface ID (0)
        """
        if not HAS_MACHINE:
            raise RuntimeError("machine module ไม่พร้อมใช้งาน")

        if phy_type not in self._PHY_MAP:
            raise ValueError(f"phy_type ต้องเป็นหนึ่งใน: {list(self._PHY_MAP.keys())}")

        if ref_clk not in self._CLOCK_MAP:
            raise ValueError(f"ref_clk ต้องเป็นหนึ่งใน: {list(self._CLOCK_MAP.keys())}")

        self._mdc = mdc
        self._mdio = mdio
        self._phy_type = phy_type
        self._phy_addr = phy_addr
        self._ref_clk = ref_clk
        self._power_pin = power_pin
        self._lan_id = lan_id
        self._lan = None
        self._connected = False
        self._config_mgr = None

        # Power control
        if power_pin is not None:
            self._power = Pin(power_pin, Pin.OUT)
            self._power.value(1)  # power on

        # Init LAN
        try:
            clock_mode = self._CLOCK_MAP[ref_clk]
            phy = self._PHY_MAP[phy_type]

            # Map to network.PHY constants
            phy_types = [
                network.PHY_LAN8720,
                network.PHY_IP101,
                network.PHY_DP83848,
                network.PHY_RTL8201,
                network.PHY_KSZ8041,
            ]

            self._lan = network.LAN(
                lan_id,
                mdc=Pin(mdc),
                mdio=Pin(mdio),
                power=Pin(power_pin) if power_pin else None,
                phy_type=phy_types[phy] if phy < len(phy_types) else network.PHY_LAN8720,
                phy_addr=phy_addr,
                ref_clk_mode=clock_mode,
            )

            print(f"🌐 Ethernet เริ่มต้น — {phy_type}, "
                  f"MDC=GPIO{mdc}, MDIO=GPIO{mdio}")

        except Exception as e:
            print(f"⚠️ Ethernet init warning: {e}")
            # May fail if network.LAN API differs between MicroPython ports

        # Load config if available
        if JsonConfigManager:
            try:
                self._config_mgr = JsonConfigManager('ethernet_config.json')
            except Exception:
                pass

    # ── Connection ────────────────────────────────────────

    def connect(self, timeout_ms: int = 15000) -> bool:
        """
        เชื่อมต่อ Ethernet (DHCP)

        :param timeout_ms: connection timeout (ms)
        :return: True ถ้าเชื่อมต่อสำเร็จ
        """
        if not self._lan:
            print("❌ Ethernet: LAN interface ไม่พร้อมใช้งาน")
            return False

        import time

        try:
            self._lan.active(True)

            # Wait for link up
            start = time.ticks_ms()
            while not self._lan.isconnected():
                if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                    print("❌ Ethernet: connection timeout")
                    self._connected = False
                    return False
                time.sleep_ms(100)

            self._connected = True
            ip, netmask, gw, dns = self._lan.ifconfig()
            print(f"🌐 Ethernet connected — IP: {ip}")
            return True

        except Exception as e:
            print(f"❌ Ethernet connect error: {e}")
            self._connected = False
            return False

    def disconnect(self) -> bool:
        """
        ยกเลิกการเชื่อมต่อ Ethernet

        :return: True ถ้าสำเร็จ
        """
        if self._lan:
            try:
                self._lan.active(False)
                self._connected = False
                print(f"🛑 Ethernet disconnected")
                return True
            except Exception as e:
                print(f"⚠️ Ethernet disconnect error: {e}")
        return False

    # ── Network Info ──────────────────────────────────────

    def ifconfig(self) -> tuple:
        """
        อ่าน network configuration

        :return: (ip, netmask, gateway, dns)
        """
        if self._lan and self._lan.active():
            return self._lan.ifconfig()
        return ('0.0.0.0', '0.0.0.0', '0.0.0.0', '0.0.0.0')

    def is_connected(self) -> bool:
        """
        ตรวจสอบว่ากำลังเชื่อมต่ออยู่หรือไม่

        :return: True ถ้าเชื่อมต่อ
        """
        if self._lan:
            return self._lan.isconnected() if hasattr(self._lan, 'isconnected') else self._connected
        return False

    @property
    def ip_address(self) -> str:
        """IP address"""
        return self.ifconfig()[0]

    @property
    def netmask(self) -> str:
        """Netmask"""
        return self.ifconfig()[1]

    @property
    def gateway(self) -> str:
        """Gateway"""
        return self.ifconfig()[2]

    @property
    def dns(self) -> str:
        """DNS server"""
        return self.ifconfig()[3]

    # ── Static IP ─────────────────────────────────────────

    def set_static(self, ip: str, netmask: str, gateway: str, dns: str = '8.8.8.8'):
        """
        ตั้งค่า static IP

        :param ip: IP address (e.g. '192.168.1.100')
        :param netmask: netmask (e.g. '255.255.255.0')
        :param gateway: gateway (e.g. '192.168.1.1')
        :param dns: DNS server (e.g. '8.8.8.8')
        """
        if self._lan:
            self._lan.ifconfig((ip, netmask, gateway, dns))
            self._connected = True
            print(f"🌐 Ethernet static IP: {ip}")
        else:
            print("❌ Ethernet: LAN ไม่พร้อม — ไม่สามารถตั้ง static IP ได้")

    # ── MAC Address ───────────────────────────────────────

    def mac_address(self) -> str:
        """
        อ่าน MAC address

        :return: MAC address string (e.g. 'AA:BB:CC:DD:EE:FF')
        """
        if self._lan:
            try:
                import ubinascii
                mac = ubinascii.hexlify(self._lan.config('mac'), ':').decode()
                return mac
            except Exception:
                pass
        return '00:00:00:00:00:00'

    # ── Async ─────────────────────────────────────────────

    async def async_connect(self, timeout_ms: int = 15000) -> bool:
        """
        Async version of connect()

        :param timeout_ms: timeout (ms)
        :return: True if connected
        """
        import time
        if not self._lan:
            print("❌ Ethernet: LAN interface ไม่พร้อมใช้งาน")
            return False

        try:
            self._lan.active(True)

            start = time.ticks_ms()
            while not self._lan.isconnected():
                if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                    print("❌ Ethernet: connection timeout")
                    self._connected = False
                    return False
                await asyncio.sleep_ms(100)

            self._connected = True
            ip = self._lan.ifconfig()[0]
            print(f"🌐 Ethernet connected — IP: {ip}")
            return True

        except Exception as e:
            print(f"❌ Ethernet async_connect error: {e}")
            self._connected = False
            return False

    # ── Cleanup ───────────────────────────────────────────

    def deinit(self):
        """ปิด Ethernet และคืนทรัพยากร"""
        self.disconnect()
        if self._power_pin is not None and hasattr(self, '_power'):
            self._power.value(0)  # power off PHY
        if self._lan:
            try:
                self._lan.active(False)
            except Exception:
                pass
            self._lan = None
        print(f"🛑 Ethernet ปิดแล้ว")
