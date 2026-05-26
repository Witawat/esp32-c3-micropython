"""
DS18B20 Temperature Sensor Driver
Interface: 1-Wire
รองรับ: ESP32 ทุกรุ่น

รองรับหลายตัวบน bus เดียวกัน (multi-drop)
"""

import machine
import onewire
import ds18x20 as _ds18x20
import time


class DS18B20:
    """
    Driver สำหรับ DS18B20 (Dallas 1-Wire temperature sensor)

    การเชื่อมต่อ:
        VCC → 3.3V
        GND → GND
        DATA → GPIO + ต่อ pull-up resistor 4.7kΩ ไปยัง VCC

    ตัวอย่าง:
        sensor = DS18B20(pin=4)
        temps = sensor.read_all()     # อ่านทุกตัวบน bus
        temp  = sensor.read()         # อ่านตัวแรก
    """

    def __init__(self, pin: int):
        """
        :param pin: หมายเลข GPIO สาย DATA (ต้องมี pull-up 4.7kΩ)
        """
        self._ow = onewire.OneWire(machine.Pin(pin))
        self._ds = _ds18x20.DS18X20(self._ow)
        self._roms = []
        self._scan()
        print(f"🌡️ DS18B20 เริ่มต้นที่ GPIO {pin} — พบ {len(self._roms)} ตัว")

    def _scan(self):
        """สแกนหา sensor ทั้งหมดบน bus"""
        self._roms = self._ds.scan()
        if not self._roms:
            print("⚠️ DS18B20 ไม่พบ sensor บน 1-Wire bus")

    def scan(self) -> list:
        """
        สแกนหา sensor ใหม่ และคืน list ของ ROM address

        :return: list ของ bytes (ROM address ของแต่ละตัว)
        """
        self._scan()
        return self._roms

    @property
    def count(self) -> int:
        """จำนวน sensor ที่พบบน bus"""
        return len(self._roms)

    def read_all(self) -> list:
        """
        อ่านอุณหภูมิทุกตัวบน bus

        :return: list ของ (rom_address_hex, temperature_c)
        """
        if not self._roms:
            print("⚠️ DS18B20 ไม่พบ sensor")
            return []
        try:
            self._ds.convert_temp()
            time.sleep_ms(750)  # รอ conversion เสร็จ
            results = []
            for rom in self._roms:
                temp = self._ds.read_temp(rom)
                results.append((rom.hex(), round(temp, 2)))
            return results
        except Exception as e:
            print(f"❌ DS18B20 อ่านค่าไม่ได้: {e}")
            return []

    def read(self, index: int = 0) -> float | None:
        """
        อ่านอุณหภูมิของ sensor ตามลำดับบน bus

        :param index: ลำดับที่ของ sensor (เริ่มจาก 0)
        :return: อุณหภูมิ °C หรือ None ถ้าผิดพลาด
        """
        results = self.read_all()
        if not results or index >= len(results):
            return None
        return results[index][1]

    def read_by_rom(self, rom: bytes) -> float | None:
        """
        อ่านอุณหภูมิโดยระบุ ROM address

        :param rom: ROM address ของ sensor (bytes)
        :return: อุณหภูมิ °C หรือ None
        """
        try:
            self._ds.convert_temp()
            time.sleep_ms(750)
            return round(self._ds.read_temp(rom), 2)
        except Exception as e:
            print(f"❌ DS18B20 read_by_rom ผิดพลาด: {e}")
            return None
