"""
Ethernet Manager สำหรับ ESP32-C3 (MicroPython)
จัดการการเชื่อมต่อ Ethernet ผ่าน external PHY (LAN8720, IP101, DP83848 ฯลฯ)

วิธีใช้งาน:
    from ethernet import EthernetManager
    eth = EthernetManager(mdc=23, mdio=18)
    eth.connect()
    print(eth.ifconfig())
"""

from ethernet.ethernet_manager import EthernetManager
