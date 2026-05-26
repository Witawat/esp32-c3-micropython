"""
DC Motor Controller — L298N / L9110 / TB6612
Interface: PWM + GPIO
รองรับ: ESP32 ทุกรุ่น

รองรับ: L298N (Dual H-Bridge), L9110S (2-channel), TB6612FNG
"""

import machine


class DCMotor:
    """
    Controller สำหรับ DC Motor ผ่าน H-Bridge driver

    การเชื่อมต่อ (L298N):
        ENA → GPIO (PWM) — ควบคุม speed
        IN1 → GPIO       — direction bit 1
        IN2 → GPIO       — direction bit 2
        OUT1/OUT2 → motor

    การเชื่อมต่อ (L9110):
        A-IA → GPIO (PWM)
        A-IB → GPIO (PWM)

    ตัวอย่าง:
        motor = DCMotor(pwm_pin=12, in1_pin=14, in2_pin=27)
        motor.forward(speed=80)   # 80% speed
        motor.backward(speed=50)
        motor.stop()
        motor.brake()
    """

    def __init__(self, pwm_pin: int, in1_pin: int, in2_pin: int,
                 freq: int = 1000,
                 min_duty: int = 0, max_duty: int = 100):
        """
        :param pwm_pin: GPIO สำหรับ PWM (ENA/ENB)
        :param in1_pin: GPIO direction 1 (IN1)
        :param in2_pin: GPIO direction 2 (IN2)
        :param freq: PWM frequency Hz
        :param min_duty: duty cycle ต่ำสุด % (ใช้ dead-band ป้องกัน motor ไม่หมุน)
        :param max_duty: duty cycle สูงสุด %
        """
        self._pwm = machine.PWM(machine.Pin(pwm_pin), freq=freq)
        self._in1 = machine.Pin(in1_pin, machine.Pin.OUT)
        self._in2 = machine.Pin(in2_pin, machine.Pin.OUT)
        self._min_duty = min_duty
        self._max_duty = max_duty
        self._speed = 0
        self.stop()
        print(f"⚙️ DCMotor เริ่มต้น PWM={pwm_pin}, IN1={in1_pin}, IN2={in2_pin}")

    def _set_duty(self, pct: int):
        """ตั้งค่า duty cycle 0–100%"""
        pct = max(0, min(100, pct))
        if 0 < pct < self._min_duty:
            pct = self._min_duty
        duty = int(pct / 100 * 65535)
        self._pwm.duty_u16(duty)
        self._speed = pct

    def forward(self, speed: int = 100):
        """
        หมุนไปข้างหน้า

        :param speed: ความเร็ว 0–100 %
        """
        self._in1.value(1)
        self._in2.value(0)
        self._set_duty(speed)

    def backward(self, speed: int = 100):
        """
        หมุนถอยหลัง

        :param speed: ความเร็ว 0–100 %
        """
        self._in1.value(0)
        self._in2.value(1)
        self._set_duty(speed)

    def stop(self):
        """หยุด (coast — ไม่มี braking)"""
        self._in1.value(0)
        self._in2.value(0)
        self._set_duty(0)

    def brake(self):
        """หยุดโดย short brake (หยุดเร็ว)"""
        self._in1.value(1)
        self._in2.value(1)
        self._set_duty(100)

    def speed(self, pct: int):
        """
        ปรับความเร็วโดยไม่เปลี่ยนทิศทาง

        :param pct: 0–100 %
        """
        self._set_duty(pct)

    @property
    def current_speed(self) -> int:
        """ความเร็วปัจจุบัน %"""
        return self._speed

    def deinit(self):
        """ปิด PWM"""
        self.stop()
        self._pwm.deinit()


class DCMotorL9110:
    """
    Controller สำหรับ L9110 / L9110S
    (ใช้ 2 PWM pin แทน 1 PWM + 2 GPIO)

    การเชื่อมต่อ:
        A-IA → GPIO (PWM) — forward control
        A-IB → GPIO (PWM) — backward control

    ตัวอย่าง:
        motor = DCMotorL9110(ia_pin=12, ib_pin=14)
        motor.forward(80)
        motor.backward(50)
        motor.stop()
    """

    def __init__(self, ia_pin: int, ib_pin: int, freq: int = 1000):
        self._ia = machine.PWM(machine.Pin(ia_pin), freq=freq)
        self._ib = machine.PWM(machine.Pin(ib_pin), freq=freq)
        self.stop()
        print(f"⚙️ DCMotor L9110 เริ่มต้น IA={ia_pin}, IB={ib_pin}")

    def forward(self, speed: int = 100):
        duty = int(max(0, min(100, speed)) / 100 * 65535)
        self._ia.duty_u16(duty)
        self._ib.duty_u16(0)

    def backward(self, speed: int = 100):
        duty = int(max(0, min(100, speed)) / 100 * 65535)
        self._ia.duty_u16(0)
        self._ib.duty_u16(duty)

    def stop(self):
        self._ia.duty_u16(0)
        self._ib.duty_u16(0)

    def deinit(self):
        self.stop()
        self._ia.deinit()
        self._ib.deinit()
