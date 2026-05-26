"""
Button Driver
Interface: GPIO + Debounce
รองรับ: ESP32 ทุกรุ่น
"""

import machine
import time
import asyncio


class PressPattern:
    """
    คลาสสำหรับกำหนดรูปแบบการกดปุ่ม
    
    รูปแบบประกอบด้วยลำดับของการกด โดยแต่ละครั้งระบุระยะเวลาขั้นต่ำและสูงสุด
    
    ตัวอย่าง:
        # กดสั้น-สั้น-ยาว (เช่น SOS pattern)
        pattern = PressPattern([
            (50, 250),   # กดครั้งแรก: 50-250ms (สั้น)
            (50, 250),   # กดครั้งที่สอง: 50-250ms (สั้น)
            (400, 1000)  # กดครั้งที่สาม: 400-1000ms (ยาว)
        ])
    """
    
    def __init__(self, durations: list, max_gap_ms: int = 500):
        """
        :param durations: list ของ tuple (min_ms, max_ms) สำหรับแต่ละครั้งการกด
        :param max_gap_ms: ระยะห่างสูงสุดระหว่างการกด (ms)
        """
        self.durations = durations
        self.max_gap_ms = max_gap_ms
        self._press_times = []
        self._last_release_ms = 0
    
    def reset(self):
        """รีเซ็ตสถานะของ pattern"""
        self._press_times = []
        self._last_release_ms = 0
    
    def record_press(self, press_time: int, release_time: int = None):
        """บันทึกเวลาการกด"""
        if release_time:
            duration = time.ticks_diff(release_time, press_time)
            self._press_times.append((press_time, release_time, duration))
        else:
            self._press_times.append((press_time, None, None))
    
    def record_release(self, release_time: int):
        """บันทึกเวลาการปล่อย"""
        if self._press_times and self._press_times[-1][1] is None:
            press_time = self._press_times[-1][0]
            duration = time.ticks_diff(release_time, press_time)
            self._press_times[-1] = (press_time, release_time, duration)
        self._last_release_ms = release_time
    
    def check_match(self) -> bool:
        """
        ตรวจสอบว่าลำดับการกดตรงกับ pattern หรือไม่
        
        :return: True ถ้าตรง, False ถ้าไม่ตรง
        """
        if len(self._press_times) != len(self.durations):
            return False
        
        for i, (press_time, release_time, duration) in enumerate(self._press_times):
            if duration is None:
                return False
            
            min_ms, max_ms = self.durations[i]
            if not (min_ms <= duration <= max_ms):
                return False
            
            # Check gap between presses
            if i > 0:
                prev_release = self._press_times[i-1][1]
                if prev_release:
                    gap = time.ticks_diff(press_time, prev_release)
                    if gap > self.max_gap_ms or gap < 0:
                        return False
        
        return True
    
    def get_progress(self) -> float:
        """รับความคืบหน้าของการจับคู่ pattern (0.0 - 1.0)"""
        if not self.durations:
            return 0.0
        return len(self._press_times) / len(self.durations)


class Button:
    """
    Driver สำหรับปุ่มกด (tactile switch)

    ตัวอย่าง:
        btn = Button(pin=9, pull='up')
        if btn.is_pressed:
            print('pressed')
        
        # Long press detection
        btn.on_long_press(lambda: print("Long pressed!"), threshold_ms=1000)
        
        # Double click detection
        btn.on_double_click(lambda: print("Double clicked!"))
        
        # Get press duration
        duration = btn.get_last_press_duration()
    """

    def __init__(self, pin: int, pull: str = "up", active_low: bool = True,
                 debounce_ms: int = 50, long_press_threshold_ms: int = 1000,
                 click_window_ms: int = 300, max_clicks: int = 5):
        self._debounce_ms = debounce_ms
        self._active_low = active_low
        self._last_irq_ms = 0
        self._press_cb = None
        self._release_cb = None
        
        # Long press detection
        self._long_press_threshold_ms = long_press_threshold_ms
        self._long_press_cb = None
        self._press_start_ms = 0
        self._long_press_triggered = False
        
        # Multi-click detection
        self._click_window_ms = click_window_ms
        self._max_clicks = max_clicks
        self._click_count = 0
        self._last_click_ms = 0
        self._multi_click_cbs = {}  # {count: callback}
        self._click_timer_task = None
        
        # Press duration tracking
        self._last_press_duration = 0
        
        # Pattern recognition
        self._registered_patterns = {}  # {name: (PressPattern, callback)}
        self._active_pattern = None
        self._pattern_task = None

        if pull == "up":
            mode = machine.Pin.PULL_UP
        elif pull == "down":
            mode = machine.Pin.PULL_DOWN
        else:
            mode = None

        if mode is None:
            self._pin = machine.Pin(pin, machine.Pin.IN)
        else:
            self._pin = machine.Pin(pin, machine.Pin.IN, mode)

    @property
    def is_pressed(self) -> bool:
        val = self._pin.value()
        return (val == 0) if self._active_low else (val == 1)

    def read(self) -> bool:
        return self.is_pressed

    def on_press(self, callback):
        self._press_cb = callback
        self._enable_irq()

    def on_release(self, callback):
        self._release_cb = callback
        self._enable_irq()

    def on_long_press(self, callback, threshold_ms: int = None):
        """
        ตั้งค่า callback สำหรับการกดค้าง
        
        :param callback: ฟังก์ชันที่จะเรียกเมื่อกดค้าง (รับพารามิเตอร์ duration_ms)
        :param threshold_ms: เกณฑ์เวลาในการถือว่าเป็นการกดค้าง (ms), None = ใช้ค่า default
        
        ตัวอย่าง:
            btn.on_long_press(lambda dur: print(f"Long pressed for {dur}ms"))
        """
        if threshold_ms is not None:
            self._long_press_threshold_ms = threshold_ms
        self._long_press_cb = callback
        self._enable_irq()

    def on_multi_click(self, count: int, callback):
        """
        ตั้งค่า callback สำหรับการกดหลายครั้ง
        
        :param count: จำนวนครั้งที่กด (2 = double click, 3 = triple click, etc.)
        :param callback: ฟังก์ชันที่จะเรียก (รับพารามิเตอร์ click_count)
        
        ตัวอย่าง:
            btn.on_multi_click(2, lambda c: print("Double clicked!"))
            btn.on_multi_click(3, lambda c: print("Triple clicked!"))
        """
        if 1 <= count <= self._max_clicks:
            self._multi_click_cbs[count] = callback
            self._enable_irq()

    def on_double_click(self, callback):
        """ตั้งค่า callback สำหรับดับเบิลคลิก"""
        self.on_multi_click(2, callback)

    def on_triple_click(self, callback):
        """ตั้งค่า callback สำหรับทริปเปิลคลิก"""
        self.on_multi_click(3, callback)

    def get_last_press_duration(self) -> int:
        """
        รับระยะเวลาการกดครั้งล่าสุด (ms)
        
        :return: ระยะเวลาที่กดค้างในหน่วย milliseconds
        """
        return self._last_press_duration

    def register_pattern(self, name: str, pattern: PressPattern, callback):
        """
        ลงทะเบียนรูปแบบการกด
        
        :param name: ชื่อของ pattern (เช่น "sos", "quick-quick-long")
        :param pattern: อ็อบเจ็กต์ PressPattern ที่กำหนดรูปแบบ
        :param callback: ฟังก์ชันที่จะเรียกเมื่อ pattern ตรง (รับพารามิเตอร์ pattern_name)
        
        ตัวอย่าง:
            pattern = PressPattern([(50, 250), (50, 250), (400, 1000)])
            btn.register_pattern("sos", pattern, lambda n: print(f"Pattern {n} detected!"))
        """
        self._registered_patterns[name] = (pattern, callback)
        self._enable_irq()

    def unregister_pattern(self, name: str):
        """ยกเลิกการลงทะเบียน pattern"""
        if name in self._registered_patterns:
            del self._registered_patterns[name]

    def clear_patterns(self):
        """ล้าง pattern ทั้งหมด"""
        self._registered_patterns.clear()
        self._active_pattern = None

    def _enable_irq(self):
        self._pin.irq(trigger=machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING,
                      handler=self._irq_handler)

    def disable_irq(self):
        self._pin.irq(handler=None)

    def _irq_handler(self, _):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_irq_ms) < self._debounce_ms:
            return
        self._last_irq_ms = now

        pressed = self.is_pressed
        if pressed and self._press_cb:
            self._press_start_ms = now
            self._long_press_triggered = False
            
            # Record press for pattern recognition
            if self._registered_patterns:
                if self._active_pattern is None:
                    # Start new pattern matching
                    self._start_pattern_matching(now)
                else:
                    # Check gap between presses
                    if self._active_pattern._last_release_ms > 0:
                        gap = time.ticks_diff(now, self._active_pattern._last_release_ms)
                        if gap > self._active_pattern.max_gap_ms or gap < 0:
                            # Gap too large, reset pattern
                            self._active_pattern.reset()
                            self._start_pattern_matching(now)
            
            self._press_cb()
        elif (not pressed) and self._release_cb:
            # Calculate press duration
            if self._press_start_ms > 0:
                self._last_press_duration = time.ticks_diff(now, self._press_start_ms)
                
                # Record release for pattern recognition
                if self._active_pattern:
                    self._active_pattern.record_release(now)
                    
                    # Check if pattern is complete
                    if self._active_pattern.check_match():
                        # Pattern matched! Find which one
                        for name, (pattern, cb) in self._registered_patterns.items():
                            if pattern is self._active_pattern:
                                if asyncio.iscoroutinefunction(cb):
                                    asyncio.create_task(cb(name))
                                else:
                                    cb(name)
                                break
                        self._active_pattern = None
            
            # Check for long press on release if not already triggered
            if self._press_start_ms > 0 and not self._long_press_triggered:
                duration = self._last_press_duration
                if duration >= self._long_press_threshold_ms and self._long_press_cb:
                    self._long_press_cb(duration)
            
            # Multi-click detection
            self._handle_click(now)
            
            self._release_cb()
            self._press_start_ms = 0
    
    def _start_pattern_matching(self, press_time: int):
        """Start tracking a new pattern"""
        # Create a temporary pattern based on registered patterns
        # For simplicity, we'll use the first registered pattern's structure
        if self._registered_patterns:
            # Use the longest pattern as template
            longest_name = max(self._registered_patterns.keys(), 
                             key=lambda k: len(self._registered_patterns[k][0].durations))
            template_pattern = self._registered_patterns[longest_name][0]
            self._active_pattern = PressPattern(
                template_pattern.durations.copy(),
                template_pattern.max_gap_ms
            )
            self._active_pattern.record_press(press_time)

    def _handle_click(self, now: int):
        """Handle multi-click detection"""
        if self._click_count == 0:
            # First click
            self._click_count = 1
            self._last_click_ms = now
            # Start timer to wait for more clicks
            if self._multi_click_cbs:
                self._click_timer_task = asyncio.create_task(self._click_timeout_task())
        else:
            # Subsequent click
            time_diff = time.ticks_diff(now, self._last_click_ms)
            if time_diff <= self._click_window_ms:
                self._click_count += 1
                self._last_click_ms = now
                # Reset timer
                if self._click_timer_task:
                    self._click_timer_task.cancel()
                if self._multi_click_cbs:
                    self._click_timer_task = asyncio.create_task(self._click_timeout_task())
            else:
                # Too slow, treat as new sequence
                self._finalize_click_count()
                self._click_count = 1
                self._last_click_ms = now
                if self._multi_click_cbs:
                    self._click_timer_task = asyncio.create_task(self._click_timeout_task())

    async def _click_timeout_task(self):
        """Wait for click window to expire and finalize click count"""
        try:
            await asyncio.sleep_ms(self._click_window_ms + 50)
            self._finalize_click_count()
        except asyncio.CancelledError:
            pass

    def _finalize_click_count(self):
        """Finalize click count and trigger callback if registered"""
        if self._click_count > 0 and self._click_count in self._multi_click_cbs:
            cb = self._multi_click_cbs[self._click_count]
            if asyncio.iscoroutinefunction(cb):
                asyncio.create_task(cb(self._click_count))
            else:
                cb(self._click_count)
        self._click_count = 0

    async def wait_press(self, poll_ms: int = 20):
        while not self.is_pressed:
            await asyncio.sleep_ms(poll_ms)
        return True

    async def wait_release(self, poll_ms: int = 20):
        while self.is_pressed:
            await asyncio.sleep_ms(poll_ms)
        return True

    async def watch(self, interval_ms: int = 30, on_press=None, on_release=None):
        last = self.is_pressed
        press_start = 0
        long_press_reported = False
        
        while True:
            cur = self.is_pressed
            now = time.ticks_ms()
            
            if cur != last:
                if cur and on_press:
                    press_start = now
                    long_press_reported = False
                    if asyncio.iscoroutinefunction(on_press):
                        await on_press()
                    else:
                        on_press()
                elif (not cur) and on_release:
                    # Calculate duration
                    if press_start > 0:
                        duration = time.ticks_diff(now, press_start)
                        self._last_press_duration = duration
                        
                        # Check long press
                        if duration >= self._long_press_threshold_ms:
                            if hasattr(on_release, '__long_press_handler__'):
                                if asyncio.iscoroutinefunction(on_release):
                                    await on_release(duration, is_long_press=True)
                                else:
                                    on_release(duration, is_long_press=True)
                    
                    if asyncio.iscoroutinefunction(on_release):
                        await on_release()
                    else:
                        on_release()
                    press_start = 0
                    long_press_reported = False
                    
                last = cur
            elif cur and press_start > 0 and not long_press_reported:
                # Check for long press while holding
                duration = time.ticks_diff(now, press_start)
                if duration >= self._long_press_threshold_ms:
                    long_press_reported = True
                    # Could emit long press event here if needed
            
            await asyncio.sleep_ms(interval_ms)
