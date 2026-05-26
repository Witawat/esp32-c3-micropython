"""
Generic UART Driver สำหรับ ESP32-C3 (MicroPython)
ให้ abstraction layer เหนือ machine.UART พร้อม async support
และ frame parsing helper

วิธีใช้งาน:
    from uart import UARTDriver
    uart = UARTDriver(uart_id=1, tx=21, rx=20, baudrate=9600)
    uart.write(b'Hello')
    data = uart.read(10)
    line = uart.readline()
"""

from uart.uart_driver import UARTDriver, FrameParser
