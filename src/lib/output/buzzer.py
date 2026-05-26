"""
Buzzer Driver (Active / Passive)
Interface: GPIO / PWM
รองรับ: ESP32 ทุกรุ่น

Active Buzzer: ส่งแค่ GPIO HIGH/LOW
Passive Buzzer: ต้องการ PWM สำหรับ frequency
"""

import machine
import asyncio
import time


# โน้ตดนตรี (Hz)
NOTES = {
    'C4': 262, 'D4': 294, 'E4': 330, 'F4': 349,
    'G4': 392, 'A4': 440, 'B4': 494,
    'C5': 523, 'D5': 587, 'E5': 659, 'F5': 698,
    'G5': 784, 'A5': 880, 'B5': 988,
    'C6': 1047,
    '-': 0,   # pause
}


class Buzzer:
    """
    Driver สำหรับ Active Buzzer (GPIO on/off)

    การเชื่อมต่อ:
        VCC → 3.3V / 5V (ตรวจสอบ spec)
        GND → GND
        I/O → GPIO

    ตัวอย่าง:
        bz = Buzzer(pin=5)
        bz.beep()
        bz.beep(count=3, on_ms=100, off_ms=100)
        await bz.async_beep()
        bz.pattern([(100, 50), (100, 50), (500, 200)], repeat=2)  # short-short-long x2
    """

    def __init__(self, pin: int, active_low: bool = False):
        """
        :param pin: GPIO pin
        :param active_low: True ถ้า buzzer ทำงานเมื่อ GPIO=LOW
        """
        self._pin = machine.Pin(pin, machine.Pin.OUT, value=0)
        self._active_low = active_low
        self._state = False
        self.off()
        print(f"🔔 Buzzer (Active) เริ่มต้นที่ GPIO {pin}")

    def _write(self, state: bool):
        if self._active_low:
            self._pin.value(0 if state else 1)
        else:
            self._pin.value(1 if state else 0)
        self._state = state

    def on(self):
        """เปิด buzzer"""
        self._write(True)

    def off(self):
        """ปิด buzzer"""
        self._write(False)

    def toggle(self):
        """สลับสถานะ"""
        self._write(not self._state)

    def beep(self, count: int = 1, on_ms: int = 200, off_ms: int = 200):
        """
        บี๊บ synchronous

        :param count: จำนวนครั้ง
        :param on_ms: ระยะเวลา ON (ms)
        :param off_ms: ระยะเวลา OFF ระหว่างบี๊บ (ms)
        """
        for i in range(count):
            self.on()
            time.sleep_ms(on_ms)
            self.off()
            if i < count - 1:
                time.sleep_ms(off_ms)

    async def async_beep(self, count: int = 1,
                         on_ms: int = 200, off_ms: int = 200):
        """
        บี๊บ asynchronous

        :param count: จำนวนครั้ง
        :param on_ms: ระยะเวลา ON (ms)
        :param off_ms: ระยะเวลา OFF ระหว่างบี๊บ (ms)
        """
        for i in range(count):
            self.on()
            await asyncio.sleep_ms(on_ms)
            self.off()
            if i < count - 1:
                await asyncio.sleep_ms(off_ms)

    def pattern(self, pattern: list, repeat: int = 1, gap_ms: int = 500):
        """
        เล่นรูปแบบเสียงที่กำหนดเอง
        
        :param pattern: list ของ tuple (on_ms, off_ms) เช่น [(100, 50), (100, 50), (500, 200)]
        :param repeat: จำนวนรอบที่เล่นซ้ำ (default 1)
        :param gap_ms: ระยะห่างระหว่างรอบ (ms)
        
        ตัวอย่าง:
            bz.pattern([(100, 50), (100, 50), (500, 200)], repeat=2)  
            # เล่น "สั้น-สั้น-ยาว" จำนวน 2 รอบ
        """
        for r in range(repeat):
            for i, (on_ms, off_ms) in enumerate(pattern):
                self.on()
                time.sleep_ms(on_ms)
                self.off()
                if i < len(pattern) - 1:
                    time.sleep_ms(off_ms)
            if r < repeat - 1 and gap_ms > 0:
                time.sleep_ms(gap_ms)

    async def async_pattern(self, pattern: list, repeat: int = 1, gap_ms: int = 500):
        """
        เล่นรูปแบบเสียงที่กำหนดเองแบบ async
        
        :param pattern: list ของ tuple (on_ms, off_ms)
        :param repeat: จำนวนรอบที่เล่นซ้ำ
        :param gap_ms: ระยะห่างระหว่างรอบ (ms)
        """
        for r in range(repeat):
            for i, (on_ms, off_ms) in enumerate(pattern):
                self.on()
                await asyncio.sleep_ms(on_ms)
                self.off()
                if i < len(pattern) - 1:
                    await asyncio.sleep_ms(off_ms)
            if r < repeat - 1 and gap_ms > 0:
                await asyncio.sleep_ms(gap_ms)

    def morse_code(self, message: str, dot_ms: int = 100, repeat: int = 1):
        """
        ส่งข้อความในรูปแบบรหัสโมส
        
        :param message: ข้อความที่ต้องการส่ง (A-Z, 0-9, space)
        :param dot_ms: ระยะเวลาของจุด (ms) - ขีดจะยาว 3 เท่า
        :param repeat: จำนวนรอบที่เล่นซ้ำ
        
        ตัวอย่าง:
            bz.morse_code("SOS")  # ... --- ...
        """
        MORSE_DICT = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
            'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
            'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
            'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
            'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
            'Z': '--..',
            '0': '-----', '1': '.----', '2': '..---', '3': '...--',
            '4': '....-', '5': '.....', '6': '-....', '7': '--...',
            '8': '---..', '9': '----.',
            ' ': ' '
        }
        
        dash_ms = dot_ms * 3
        intra_char_gap = dot_ms
        inter_char_gap = dot_ms * 3
        word_gap = dot_ms * 7
        
        for r in range(repeat):
            for char_idx, char in enumerate(message.upper()):
                if char not in MORSE_DICT:
                    continue
                
                code = MORSE_DICT[char]
                
                if code == ' ':
                    time.sleep_ms(word_gap)
                    continue
                
                for symbol_idx, symbol in enumerate(code):
                    if symbol == '.':
                        self.on()
                        time.sleep_ms(dot_ms)
                        self.off()
                    elif symbol == '-':
                        self.on()
                        time.sleep_ms(dash_ms)
                        self.off()
                    
                    if symbol_idx < len(code) - 1:
                        time.sleep_ms(intra_char_gap)
                
                if char_idx < len(message) - 1 and message[char_idx + 1] != ' ':
                    time.sleep_ms(inter_char_gap)
            
            if r < repeat - 1:
                time.sleep_ms(word_gap * 2)

    async def async_morse_code(self, message: str, dot_ms: int = 100, repeat: int = 1):
        """
        ส่งข้อความในรูปแบบรหัสโมสแบบ async
        
        :param message: ข้อความที่ต้องการส่ง
        :param dot_ms: ระยะเวลาของจุด (ms)
        :param repeat: จำนวนรอบที่เล่นซ้ำ
        """
        MORSE_DICT = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
            'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
            'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
            'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
            'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
            'Z': '--..',
            '0': '-----', '1': '.----', '2': '..---', '3': '...--',
            '4': '....-', '5': '.....', '6': '-....', '7': '--...',
            '8': '---..', '9': '----.',
            ' ': ' '
        }
        
        dash_ms = dot_ms * 3
        intra_char_gap = dot_ms
        inter_char_gap = dot_ms * 3
        word_gap = dot_ms * 7
        
        for r in range(repeat):
            for char_idx, char in enumerate(message.upper()):
                if char not in MORSE_DICT:
                    continue
                
                code = MORSE_DICT[char]
                
                if code == ' ':
                    await asyncio.sleep_ms(word_gap)
                    continue
                
                for symbol_idx, symbol in enumerate(code):
                    if symbol == '.':
                        self.on()
                        await asyncio.sleep_ms(dot_ms)
                        self.off()
                    elif symbol == '-':
                        self.on()
                        await asyncio.sleep_ms(dash_ms)
                        self.off()
                    
                    if symbol_idx < len(code) - 1:
                        await asyncio.sleep_ms(intra_char_gap)
                
                if char_idx < len(message) - 1 and message[char_idx + 1] != ' ':
                    await asyncio.sleep_ms(inter_char_gap)
            
            if r < repeat - 1:
                await asyncio.sleep_ms(word_gap * 2)

    def alarm_sequence(self, stages: int = 3, base_freq_ms: int = 100, 
                       increment_ms: int = 50, repeat: int = 1):
        """
        เล่นเสียงเตือนแบบเพิ่มขึ้นเรื่อยๆ
        
        :param stages: จำนวนขั้นของความถี่
        :param base_freq_ms: ระยะเวลาเริ่มต้น (ms)
        :param increment_ms: จำนวนที่เพิ่มขึ้นในแต่ละขั้น
        :param repeat: จำนวนรอบที่เล่นซ้ำ
        
        ตัวอย่าง:
            bz.alarm_sequence(stages=3, base_freq_ms=100, increment_ms=50)
            # เล่น 100ms, 150ms, 200ms แล้วหยุด
        """
        for r in range(repeat):
            for stage in range(stages):
                duration = base_freq_ms + (stage * increment_ms)
                self.beep(count=1, on_ms=duration, off_ms=duration)
            if r < repeat - 1:
                time.sleep_ms(base_freq_ms * 2)

    async def async_alarm_sequence(self, stages: int = 3, base_freq_ms: int = 100,
                                    increment_ms: int = 50, repeat: int = 1):
        """
        เล่นเสียงเตือนแบบเพิ่มขึ้นเรื่อยๆ แบบ async
        
        :param stages: จำนวนขั้นของความถี่
        :param base_freq_ms: ระยะเวลาเริ่มต้น (ms)
        :param increment_ms: จำนวนที่เพิ่มขึ้นในแต่ละขั้น
        :param repeat: จำนวนรอบที่เล่นซ้ำ
        """
        for r in range(repeat):
            for stage in range(stages):
                duration = base_freq_ms + (stage * increment_ms)
                await self.async_beep(count=1, on_ms=duration, off_ms=duration)
            if r < repeat - 1:
                await asyncio.sleep_ms(base_freq_ms * 2)


class PassiveBuzzer:
    """
    Driver สำหรับ Passive Buzzer (PWM — สามารถเล่น tone ได้)

    การเชื่อมต่อ:
        VCC → 3.3V / 5V
        GND → GND
        I/O → GPIO (PWM capable)

    ตัวอย่าง:
        bz = PassiveBuzzer(pin=5)
        bz.tone(440, duration_ms=500)     # เสียง A4 0.5 วินาที
        bz.melody([('C4',200),('E4',200),('G4',400)])
        await bz.async_tone(880, 300)
        bz.melody([('C4',200),('E4',200)], repeat=3, volume=49152)  # เล่น 3 รอบ, volume 75%
    """

    def __init__(self, pin: int, default_volume: int = 32768):
        """
        :param pin: GPIO pin (PWM capable)
        :param default_volume: ระดับเสียงเริ่มต้น (0-65535, default 50%)
        """
        self._pin_num = pin
        self._pwm = None
        self._default_volume = default_volume
        self._current_volume = default_volume
        print(f"🎵 PassiveBuzzer เริ่มต้นที่ GPIO {pin} (volume: {default_volume})")

    def _get_pwm(self, freq: int) -> machine.PWM:
        if self._pwm is None:
            self._pwm = machine.PWM(machine.Pin(self._pin_num),
                                    freq=freq, duty_u16=self._current_volume)
        else:
            self._pwm.freq(freq)
            self._pwm.duty_u16(self._current_volume)
        return self._pwm

    def set_volume(self, volume: int):
        """
        ตั้งค่าระดับเสียง
        
        :param volume: ระดับเสียง 0-65535 (0 = เงียบ, 65535 = ดังสุด)
        
        ตัวอย่าง:
            bz.set_volume(49152)  # 75% volume
            bz.set_volume(16384)  # 25% volume
        """
        self._current_volume = max(0, min(65535, volume))
        if self._pwm:
            self._pwm.duty_u16(self._current_volume)

    def tone(self, freq: int, duration_ms: int = 0):
        """
        เล่น tone ตาม frequency

        :param freq: ความถี่ Hz (0 = หยุด)
        :param duration_ms: ระยะเวลา ms (0 = ต่อเนื่อง)
        """
        if freq <= 0:
            self.off()
            if duration_ms > 0:
                time.sleep_ms(duration_ms)
            return
        self._get_pwm(freq)
        if duration_ms > 0:
            time.sleep_ms(duration_ms)
            self.off()

    def off(self):
        """หยุดเสียง"""
        if self._pwm:
            self._pwm.duty_u16(0)

    def note(self, note_name: str, duration_ms: int = 200):
        """
        เล่นโน้ตดนตรี

        :param note_name: ชื่อโน้ต เช่น 'C4', 'A5', '-' (pause)
        :param duration_ms: ระยะเวลา ms
        """
        freq = NOTES.get(note_name.upper(), 0)
        self.tone(freq, duration_ms)

    def melody(self, notes: list, gap_ms: int = 50, repeat: int = 1, 
               volume: int = None):
        """
        เล่นทำนอง

        :param notes: list ของ (note_name, duration_ms) เช่น [('C4',200),('E4',200)]
        :param gap_ms: เว้นระหว่างโน้ต (ms)
        :param repeat: จำนวนรอบที่เล่นซ้ำ (default 1)
        :param volume: ระดับเสียงสำหรับรอบนี้ (0-65535, None = ใช้ค่า default)
        
        ตัวอย่าง:
            bz.melody([('C4',200),('E4',200),('G4',400)], repeat=2, volume=49152)
        """
        if volume is not None:
            old_volume = self._current_volume
            self.set_volume(volume)
        
        for r in range(repeat):
            for i, (note_name, duration) in enumerate(notes):
                self.note(note_name, duration)
                if i < len(notes) - 1 and gap_ms > 0:
                    time.sleep_ms(gap_ms)
            if r < repeat - 1 and gap_ms > 0:
                time.sleep_ms(gap_ms * 2)
        
        if volume is not None:
            self.set_volume(old_volume)

    async def async_tone(self, freq: int, duration_ms: int):
        """เล่น tone แบบ async"""
        if freq <= 0:
            self.off()
            await asyncio.sleep_ms(duration_ms)
            return
        self._get_pwm(freq)
        await asyncio.sleep_ms(duration_ms)
        self.off()

    async def async_melody(self, notes: list, gap_ms: int = 50, repeat: int = 1,
                           volume: int = None):
        """
        เล่นทำนองแบบ async

        :param notes: list ของ (note_name, duration_ms)
        :param gap_ms: เว้นระหว่างโน้ต
        :param repeat: จำนวนรอบที่เล่นซ้ำ
        :param volume: ระดับเสียงสำหรับรอบนี้ (0-65535, None = ใช้ค่า default)
        """
        if volume is not None:
            old_volume = self._current_volume
            self.set_volume(volume)
        
        for r in range(repeat):
            for i, (note_name, duration) in enumerate(notes):
                freq = NOTES.get(note_name.upper(), 0)
                await self.async_tone(freq, duration)
                if i < len(notes) - 1 and gap_ms > 0:
                    await asyncio.sleep_ms(gap_ms)
            if r < repeat - 1 and gap_ms > 0:
                await asyncio.sleep_ms(gap_ms * 2)
        
        if volume is not None:
            self.set_volume(old_volume)

    def pattern_melody(self, patterns: list, gap_ms: int = 100, repeat: int = 1):
        """
        เล่นทำนองที่มีรูปแบบซับซ้อน (กลุ่มโน้ต + ระยะพัก)
        
        :param patterns: list ของ tuple (notes_list, pause_ms) 
                        เช่น [([('C4',200),('E4',200)], 300), ([('G4',400)], 500)]
        :param gap_ms: เว้นระหว่างโน้ตในกลุ่มเดียวกัน
        :param repeat: จำนวนรอบที่เล่นซ้ำ
        
        ตัวอย่าง:
            bz.pattern_melody([
                ([('C4',100),('E4',100)], 200),  # กลุ่มที่ 1 + พัก 200ms
                ([('G4',400)], 500)               # กลุ่มที่ 2 + พัก 500ms
            ], repeat=2)
        """
        for r in range(repeat):
            for pattern_idx, (notes, pause) in enumerate(patterns):
                for note_name, duration in notes:
                    self.note(note_name, duration)
                    if gap_ms > 0:
                        time.sleep_ms(gap_ms)
                if pause > 0:
                    time.sleep_ms(pause)
            if r < repeat - 1:
                time.sleep_ms(500)

    async def async_pattern_melody(self, patterns: list, gap_ms: int = 100, 
                                    repeat: int = 1):
        """
        เล่นทำนองที่มีรูปแบบซับซ้อนแบบ async
        
        :param patterns: list ของ tuple (notes_list, pause_ms)
        :param gap_ms: เว้นระหว่างโน้ตในกลุ่มเดียวกัน
        :param repeat: จำนวนรอบที่เล่นซ้ำ
        """
        for r in range(repeat):
            for pattern_idx, (notes, pause) in enumerate(patterns):
                for note_name, duration in notes:
                    freq = NOTES.get(note_name.upper(), 0)
                    await self.async_tone(freq, duration)
                    if gap_ms > 0:
                        await asyncio.sleep_ms(gap_ms)
                if pause > 0:
                    await asyncio.sleep_ms(pause)
            if r < repeat - 1:
                await asyncio.sleep_ms(500)

    def deinit(self):
        """ปิด PWM"""
        if self._pwm:
            self._pwm.deinit()
            self._pwm = None
