"""
CAN Bus Module สำหรับ ESP32-C3 (MicroPython)
รองรับ CAN 2.0 (Standard 11-bit + Extended 29-bit IDs)

วิธีใช้งาน:
    from can import CANManager
    can = CANManager(rx=1, tx=2, baudrate=500000)
    can.send(0x123, b'\x01\x02\x03')
    frame = can.read()
"""

from can.can_manager import CANManager, CANFrame
