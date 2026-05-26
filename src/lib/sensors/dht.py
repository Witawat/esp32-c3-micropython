"""
DHT Sensor Driver — DHT11 / DHT22
Interface: 1-Wire Digital (GPIO)
รองรับ: ESP32 ทุกรุ่น
"""

import dht as _dht
import machine


class DHTSensor:
    """
    Driver สำหรับ DHT11 และ DHT22

    การเชื่อมต่อ:
        VCC → 3.3V หรือ 5V
        GND → GND
        DATA → GPIO (ระบุใน pin)

    ตัวอย่าง:
        sensor = DHTSensor(pin=4, model='DHT22')
        temp, hum = sensor.read()
    """

    MODEL_DHT11 = 'DHT11'
    MODEL_DHT22 = 'DHT22'

    def __init__(self, pin: int, model: str = 'DHT22'):
        """
        :param pin: หมายเลข GPIO ที่ต่อสาย DATA
        :param model: 'DHT11' หรือ 'DHT22'
        """
        self._pin = machine.Pin(pin)
        self._model = model.upper()
        if self._model == self.MODEL_DHT11:
            self._sensor = _dht.DHT11(self._pin)
        else:
            self._sensor = _dht.DHT22(self._pin)
        print(f"🌡️ DHTSensor ({self._model}) เริ่มต้นที่ GPIO {pin}")

    def read(self) -> tuple:
        """
        อ่านค่าอุณหภูมิและความชื้น

        :return: (temperature_c, humidity_percent) หรือ (None, None) ถ้าผิดพลาด
        """
        try:
            self._sensor.measure()
            temp = self._sensor.temperature()
            hum = self._sensor.humidity()
            return temp, hum
        except Exception as e:
            print(f"❌ DHTSensor อ่านค่าไม่ได้: {e}")
            return None, None

    @property
    def temperature(self) -> float | None:
        """อุณหภูมิเป็น °C"""
        temp, _ = self.read()
        return temp

    @property
    def humidity(self) -> float | None:
        """ความชื้นสัมพัทธ์ เป็น %"""
        _, hum = self.read()
        return hum

    def read_fahrenheit(self) -> tuple:
        """
        อ่านค่าอุณหภูมิเป็น °F และความชื้น

        :return: (temperature_f, humidity_percent)
        """
        temp_c, hum = self.read()
        if temp_c is None:
            return None, None
        return round(temp_c * 9 / 5 + 32, 1), hum
