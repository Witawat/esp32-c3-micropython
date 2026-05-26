"""
IR Remote — Transmit & Receive (NEC / Sony SIRC / RC5 / RAW)
Interface: GPIO (TX via PWM carrier, RX via interrupt timing)
รองรับ: ESP32 ทุกรุ่น

Protocols:
- NEC (38kHz carrier): ใช้กับรีโมททีวี/เครื่องเสียงทั่วไป
- Sony SIRC (40kHz): 12/15/20-bit
- RC5 (36kHz): Philips protocol
- RAW: บันทึก/เล่น pulse train ดิบ (ใช้กับรีโมทแอร์)
"""

import machine
import time
import asyncio

try:
    from machine import Pin, PWM, Timer
except ImportError:
    pass


# ── Protocol Constants ─────────────────────────────────────
CARRIER_NEC  = 38000
CARRIER_SONY = 40000
CARRIER_RC5  = 36000

# NEC timing (µs)
NEC_LEADER_HIGH = 9000
NEC_LEADER_LOW  = 4500
NEC_REPEAT_LOW  = 2250
NEC_BIT_HIGH    = 560
NEC_BIT_0_LOW   = 560
NEC_BIT_1_LOW   = 1690

# Sony SIRC timing (µs)
SONY_LEADER_HIGH = 2400
SONY_LEADER_LOW  = 600
SONY_BIT_HIGH    = 600
SONY_BIT_0_LOW   = 600
SONY_BIT_1_LOW   = 1200

# RC5 timing (µs) — bi-phase (Manchester) at 36kHz
RC5_HALF_BIT = 889

# Tolerance for pulse matching
TIMING_TOLERANCE = 0.30  # ±30%


class IRTransmitter:
    """
    ส่งสัญญาณ IR ผ่าน LED — รองรับ NEC, Sony SIRC, RAW

    การเชื่อมต่อ:
        IR LED Anode    → GPIO (ผ่าน resistor 100Ω)
        IR LED Cathode  → GND

    ตัวอย่าง:
        ir = IRTransmitter(pin=17)
        ir.send_nec(address=0x00, command=0x45)  # ส่ง NEC
        ir.send_sony(command=0x1A, bits=12)       # ส่ง Sony 12-bit
    """

    def __init__(self, pin: int, carrier_freq: int = CARRIER_NEC, duty: int = 512):
        """
        :param pin: GPIO สำหรับ IR LED
        :param carrier_freq: ความถี่ carrier (Hz)
        :param duty: PWM duty cycle (0-1023, 50% ≈ 512)
        """
        self._pin = pin
        self._carrier_freq = carrier_freq
        self._duty = duty
        try:
            self._pwm = PWM(Pin(pin), freq=carrier_freq, duty=0)
        except Exception as e:
            raise RuntimeError(f"❌ IR PWM init failed on pin {pin}: {e}")
        print(f"📡 IRTransmitter เริ่มต้นที่ GPIO {pin}, carrier={carrier_freq}Hz")

    def _carrier_on(self):
        self._pwm.duty(self._duty)

    def _carrier_off(self):
        self._pwm.duty(0)

    def _mark(self, us: int):
        """ส่ง carrier (mark)"""
        self._carrier_on()
        time.sleep_us(us)

    def _space(self, us: int):
        """หยุด carrier (space)"""
        self._carrier_off()
        time.sleep_us(us)

    # ── NEC Protocol ──────────────────────────────────
    def send_nec(self, address: int, command: int, repeat: int = 0):
        """
        ส่ง NEC protocol (32-bit: address + ~address + command + ~command)

        :param address: 8-bit address (0x00-0xFF)
        :param command: 8-bit command (0x00-0xFF)
        :param repeat: จำนวน repeat (0 = ส่งครั้งเดียว)
        """
        self.set_carrier(CARRIER_NEC)

        # Leader
        self._mark(NEC_LEADER_HIGH)
        self._space(NEC_LEADER_LOW)

        # Data: address (8) + address_inverse (8) + command (8) + command_inverse (8)
        self._send_nec_byte(address)
        self._send_nec_byte(address ^ 0xFF)
        self._send_nec_byte(command)
        self._send_nec_byte(command ^ 0xFF)

        # Stop bit
        self._mark(NEC_BIT_HIGH)
        self._carrier_off()

        # Repeats
        for _ in range(repeat):
            time.sleep_ms(40)  # gap between repeats
            self._mark(NEC_LEADER_HIGH)
            self._space(NEC_REPEAT_LOW)
            self._mark(NEC_BIT_HIGH)
            self._carrier_off()

    def _send_nec_byte(self, byte: int):
        """Send one byte, LSB first"""
        for i in range(8):
            self._mark(NEC_BIT_HIGH)
            if byte & (1 << i):
                self._space(NEC_BIT_1_LOW)
            else:
                self._space(NEC_BIT_0_LOW)

    # ── Sony SIRC Protocol ────────────────────────────
    def send_sony(self, command: int, bits: int = 12, address: int = 0):
        """
        ส่ง Sony SIRC protocol

        Sony SIRC มี 3 รูปแบบ:
        - 12-bit: 7 command + 5 address
        - 15-bit: 7 command + 8 address
        - 20-bit: 7 command + 5 address + 8 extended

        :param command: 7-bit command
        :param bits: 12, 15, หรือ 20
        :param address: address bits (5 หรือ 8)
        """
        self.set_carrier(CARRIER_SONY)

        # Leader
        self._mark(SONY_LEADER_HIGH)
        self._space(SONY_LEADER_LOW)

        # Encode data (LSB first)
        if bits == 12:
            data = command | (address << 7)
            n_bits = 12
        elif bits == 15:
            data = command | (address << 7)
            n_bits = 15
        elif bits == 20:
            data = command | ((address & 0x1F) << 7) | ((address >> 5) << 12)
            n_bits = 20
        else:
            raise ValueError("bits ต้องเป็น 12, 15, หรือ 20")

        for i in range(n_bits):
            self._mark(SONY_BIT_HIGH)
            if data & (1 << i):
                self._space(SONY_BIT_1_LOW)
            else:
                self._space(SONY_BIT_0_LOW)

        self._carrier_off()

    # ── RC5 Protocol ──────────────────────────────────
    def send_rc5(self, address: int, command: int):
        """
        ส่ง Philips RC5 protocol
        Bi-phase (Manchester) encoding

        :param address: 5-bit address
        :param command: 6-bit command
        """
        self.set_carrier(CARRIER_RC5)
        half = RC5_HALF_BIT

        # Start bits (2)
        self._space(half)  # S1 = 0 (space first)
        self._mark(half)   # S2 = 1

        # Toggle bit (receiver uses this to detect new press)
        toggle = 0

        # Encode: toggle(1) + address(5) + command(6)
        data = (toggle << 11) | ((address & 0x1F) << 6) | (command & 0x3F)

        for i in range(12, -1, -1):
            bit = (data >> i) & 1
            if bit == 0:
                self._mark(half)
                self._space(half)
            else:
                self._space(half)
                self._mark(half)

        self._carrier_off()

    # ── RAW Mode ──────────────────────────────────────
    def send_raw(self, pulses: list, carrier_freq: int = CARRIER_NEC):
        """
        ส่ง RAW pulse train

        :param pulses: list of (mark_us, space_us) หรือ list of int (pulse widths)
        :param carrier_freq: carrier frequency
        """
        self.set_carrier(carrier_freq)

        if pulses and isinstance(pulses[0], (list, tuple)):
            # [(mark, space), (mark, space), ...]
            for mark_us, space_us in pulses:
                self._mark(mark_us)
                self._space(space_us)
        else:
            # [pulse, pulse, ...] — alternate mark/space
            for i, us in enumerate(pulses):
                if i % 2 == 0:
                    self._mark(us)
                else:
                    self._space(us)

        self._carrier_off()

    # ── Utility ───────────────────────────────────────
    def set_carrier(self, freq: int):
        """เปลี่ยน carrier frequency"""
        if freq != self._carrier_freq:
            self._carrier_freq = freq
            self._pwm.freq(freq)

    def deinit(self):
        """Cleanup PWM"""
        self._pwm.deinit()
        print("📡 IRTransmitter deinitialized")


class IRReceiver:
    """
    รับสัญญาณ IR — ถอดรหัส NEC, Sony SIRC, RC5, และ RAW

    การเชื่อมต่อ:
        IR Receiver (VS1838 / TSOP38238):
        VOUT → GPIO
        GND  → GND
        VCC  → 3.3V

    ตัวอย่าง:
        def on_nec(address, command, raw):
            print(f"NEC: addr=0x{address:02X}, cmd=0x{command:02X}")

        ir = IRReceiver(pin=16, nec_callback=on_nec)
        await ir.listen()
    """

    def __init__(self, pin: int,
                 nec_callback=None, sony_callback=None,
                 rc5_callback=None, raw_callback=None,
                 buffer_size: int = 200):
        """
        :param pin: GPIO สำหรับ IR receiver output
        :param nec_callback: fn(address, command, raw_pulses)
        :param sony_callback: fn(command, bits, raw_pulses)
        :param rc5_callback: fn(address, command, raw_pulses)
        :param raw_callback: fn(pulses) — เมื่อ decodeไม่ได้
        :param buffer_size: ขนาด buffer สำหรับเก็บ pulse widths
        """
        self._pin = Pin(pin, Pin.IN)
        self._buf_size = buffer_size
        self._nec_cb = nec_callback
        self._sony_cb = sony_callback
        self._rc5_cb = rc5_callback
        self._raw_cb = raw_callback
        self._pulses = [0] * buffer_size
        self._pulse_idx = 0
        self._last_time = 0
        self._listening = False
        self._listen_task = None

        print(f"📡 IRReceiver เริ่มต้นที่ GPIO {pin}")

    # ── Timing Helpers ────────────────────────────────
    @staticmethod
    def _in_range(value: int, target: int, tolerance: float = TIMING_TOLERANCE) -> bool:
        """ตรวจสอบว่า value อยู่ในช่วง target ± tolerance"""
        return abs(value - target) <= target * tolerance

    def _reset_buffer(self):
        self._pulse_idx = 0
        self._last_time = time.ticks_us()

    def _record_pulse(self):
        """บันทึก pulse width (เรียกจาก interrupt)"""
        now = time.ticks_us()
        width = time.ticks_diff(now, self._last_time)
        self._last_time = now

        if self._pulse_idx < self._buf_size:
            self._pulses[self._pulse_idx] = width
            self._pulse_idx += 1

    # ── Decoders ──────────────────────────────────────
    def _decode_nec(self) -> bool:
        """ลอง decode เป็น NEC protocol"""
        idx = self._pulse_idx
        if idx < 68:  # at least one full frame
            return False

        p = self._pulses

        # Check leader
        if not (self._in_range(p[0], NEC_LEADER_HIGH) and self._in_range(p[1], NEC_LEADER_LOW)):
            return False

        # Decode 32 bits (each bit = mark + space)
        bit_start = 2
        value = 0
        for i in range(32):
            mark = p[bit_start + i * 2]
            space = p[bit_start + i * 2 + 1]
            if self._in_range(mark, NEC_BIT_HIGH):
                if self._in_range(space, NEC_BIT_1_LOW):
                    value |= (1 << i)
                elif not self._in_range(space, NEC_BIT_0_LOW):
                    return False
            else:
                return False

        address = value & 0xFF
        addr_inv = (value >> 8) & 0xFF
        command = (value >> 16) & 0xFF
        cmd_inv = (value >> 24) & 0xFF

        # Verify inverse
        if address != (addr_inv ^ 0xFF) or command != (cmd_inv ^ 0xFF):
            return False

        if self._nec_cb:
            pulses = p[:bit_start + 64]
            self._nec_cb(address, command, pulses)

        return True

    def _decode_sony(self) -> bool:
        """ลอง decode เป็น Sony SIRC protocol"""
        idx = self._pulse_idx
        if idx < 24:
            return False

        p = self._pulses

        # Check leader
        if not (self._in_range(p[0], SONY_LEADER_HIGH) and self._in_range(p[1], SONY_LEADER_LOW)):
            return False

        # Count bits (12, 15, or 20)
        bit_count = (idx - 2) // 2
        if bit_count not in (12, 15, 20):
            return False

        value = 0
        for i in range(bit_count):
            mark = p[2 + i * 2]
            space = p[2 + i * 2 + 1]
            if self._in_range(mark, SONY_BIT_HIGH):
                if self._in_range(space, SONY_BIT_1_LOW):
                    value |= (1 << i)
                elif not self._in_range(space, SONY_BIT_0_LOW):
                    return False
            else:
                return False

        command = value & 0x7F

        if self._sony_cb:
            pulses = p[:2 + bit_count * 2]
            self._sony_cb(command, bit_count, pulses)

        return True

    # ── Sync Capture ──────────────────────────────────
    def capture(self, timeout_ms: int = 200) -> bool:
        """
        จับ IR signal แบบ sync (blocking)

        :param timeout_ms: timeout รอ Leader pulse
        :return: True ถ้าจับ + decode ได้
        """
        self._reset_buffer()

        # Wait for first edge (leader)
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while self._pin.value() == 1:  # idle HIGH (pull-up)
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                return False
            time.sleep_us(10)

        self._last_time = time.ticks_us()

        # Record pulse train
        last_val = 0
        deadline = time.ticks_add(time.ticks_ms(), 200)  # max capture 200ms
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            val = self._pin.value()
            if val != last_val:
                self._record_pulse()
                last_val = val
            time.sleep_us(10)
            if self._pulse_idx >= self._buf_size:
                break

        # Try decoders
        if self._decode_nec():
            return True
        if self._decode_sony():
            return True
        # TODO: RC5 decode

        # RAW callback
        if self._raw_cb and self._pulse_idx > 4:
            self._raw_cb(self._pulses[:self._pulse_idx])
            return True

        return False

    # ── Async Listen ──────────────────────────────────
    async def listen(self, active_low: bool = True):
        """
        เริ่มรับ IR signal แบบ async

        :param active_low: True ถ้า receiver active LOW (VS1838=active LOW)
        """
        self._listening = True
        print("📡 IRReceiver เริ่มฟัง...")
        try:
            while self._listening:
                # Wait for signal (active LOW)
                while self._pin.value() == (1 if active_low else 0):
                    await asyncio.sleep_ms(1)

                self.capture(timeout_ms=50)
                await asyncio.sleep_ms(50)
        except asyncio.CancelledError:
            print("📡 IRReceiver หยุดฟัง")

    def start_listening(self, active_low: bool = True):
        """
        เริ่ม async listen loop (non-blocking)

        :param active_low: True ถ้า receiver active LOW
        """
        self._listen_task = asyncio.create_task(self.listen(active_low))

    def stop_listening(self):
        """หยุด async listen"""
        self._listening = False
        if self._listen_task:
            self._listen_task.cancel()
            self._listen_task = None
            print("📡 IRReceiver หยุดฟัง")

    def deinit(self):
        """Cleanup"""
        self.stop_listening()
        print("📡 IRReceiver deinitialized")

    def get_raw_pulses(self) -> list:
        """คืนค่า RAW pulse train ที่จับได้ล่าสุด"""
        return self._pulses[:self._pulse_idx]
