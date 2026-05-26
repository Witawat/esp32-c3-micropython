"""
ตัวอย่างการใช้งาน Buzzer Patterns และฟีเจอร์ขั้นสูง

สาธิตการใช้งาน:
- Pattern playback (รูปแบบเสียงที่กำหนดเอง)
- Morse code transmission
- Alarm sequences (เสียงเตือนแบบเพิ่มขึ้น)
- Melody repetition และ volume control
"""

import sys
sys.path.insert(0, '/lib')

from output.buzzer import Buzzer, PassiveBuzzer
import asyncio


async def demo_active_buzzer_patterns():
    """สาธิต Active Buzzer พร้อมรูปแบบเสียง"""
    print("\n🔔 === Active Buzzer Pattern Demo ===")
    
    # สร้าง Buzzer ที่ GPIO 5
    bz = Buzzer(pin=5)
    
    # ตัวอย่างที่ 1: รูปแบบ "สั้น-สั้น-ยาว" (เหมือน SOS)
    print("Playing: Short-Short-Long pattern x2")
    bz.pattern([
        (100, 50),   # สั้น 100ms, พัก 50ms
        (100, 50),   # สั้น 100ms, พัก 50ms
        (500, 200)   # ยาว 500ms, พัก 200ms
    ], repeat=2, gap_ms=1000)
    
    await asyncio.sleep(1)
    
    # ตัวอย่างที่ 2: Morse code "SOS"
    print("Playing: SOS in Morse code")
    bz.morse_code("SOS", dot_ms=100, repeat=2)
    
    await asyncio.sleep(1)
    
    # ตัวอย่างที่ 3: Alarm sequence (เสียงเพิ่มขึ้น)
    print("Playing: Alarm sequence")
    bz.alarm_sequence(stages=4, base_freq_ms=100, increment_ms=50, repeat=2)
    
    await asyncio.sleep(1)
    
    # ตัวอย่างที่ 4: Async pattern
    print("Playing: Async pattern")
    await bz.async_pattern([
        (50, 30),
        (50, 30),
        (50, 30),
        (200, 100)
    ], repeat=3)
    
    print("✅ Active Buzzer demo complete\n")


async def demo_passive_buzzer_advanced():
    """สาธิต Passive Buzzer พร้อม melody และ volume control"""
    print("\n🎵 === Passive Buzzer Advanced Demo ===")
    
    # สร้าง PassiveBuzzer ที่ GPIO 18
    bz = PassiveBuzzer(pin=18, default_volume=32768)  # 50% volume
    
    # ตัวอย่างที่ 1: เล่นทำนองซ้ำหลายรอบ
    print("Playing: Simple melody x3")
    bz.melody([
        ('C4', 200),
        ('E4', 200),
        ('G4', 400)
    ], gap_ms=50, repeat=3)
    
    await asyncio.sleep(1)
    
    # ตัวอย่างที่ 2: เปลี่ยนระดับเสียง
    print("Playing: Melody with different volumes")
    bz.set_volume(16384)  # 25% volume - เบา
    bz.note('C4', 300)
    await asyncio.sleep_ms(100)
    
    bz.set_volume(32768)  # 50% volume - ปานกลาง
    bz.note('E4', 300)
    await asyncio.sleep_ms(100)
    
    bz.set_volume(49152)  # 75% volume - ดัง
    bz.note('G4', 300)
    await asyncio.sleep_ms(100)
    
    bz.set_volume(65535)  # 100% volume - ดังสุด
    bz.note('C5', 300)
    
    await asyncio.sleep(1)
    
    # ตัวอย่างที่ 3: Pattern melody (กลุ่มโน้ตซับซ้อน)
    print("Playing: Complex pattern melody")
    bz.pattern_melody([
        ([('C4', 100), ('E4', 100)], 200),   # กลุ่มที่ 1 + พัก 200ms
        ([('G4', 200)], 300),                 # กลุ่มที่ 2 + พัก 300ms
        ([('C5', 100), ('G4', 100), ('E4', 100)], 400)  # กลุ่มที่ 3 + พัก 400ms
    ], gap_ms=50, repeat=2)
    
    await asyncio.sleep(1)
    
    # ตัวอย่างที่ 4: Async melody with volume
    print("Playing: Async melody with custom volume")
    await bz.async_melody([
        ('A4', 200),
        ('B4', 200),
        ('C5', 400)
    ], gap_ms=50, repeat=2, volume=49152)
    
    # ปิด PWM
    bz.deinit()
    
    print("✅ Passive Buzzer demo complete\n")


async def demo_practical_applications():
    """สาธิตการใช้งานจริง"""
    print("\n📱 === Practical Applications Demo ===")
    
    bz = Buzzer(pin=5)
    
    # สถานการณ์ที่ 1: แจ้งเตือนแบตเตอรี่ต่ำ
    print("Scenario 1: Low battery warning")
    bz.pattern([(100, 50), (100, 50)], repeat=3, gap_ms=2000)
    await asyncio.sleep(1)
    
    # สถานการณ์ที่ 2: ยืนยันการกดปุ่ม
    print("Scenario 2: Button press confirmation")
    bz.beep(count=1, on_ms=50, off_ms=0)
    await asyncio.sleep_ms(200)
    
    # สถานการณ์ที่ 3: ข้อผิดพลาด
    print("Scenario 3: Error alert")
    bz.pattern([(200, 100), (200, 100), (200, 100)], repeat=2)
    await asyncio.sleep(1)
    
    # สถานการณ์ที่ 4: Morse code สำหรับสถานะ
    print("Scenario 4: Status codes via Morse")
    print("  - OK: .- (A)")
    bz.morse_code("A", dot_ms=80)
    await asyncio.sleep_ms(500)
    
    print("  - ERROR: . (E)")
    bz.morse_code("E", dot_ms=80)
    await asyncio.sleep(1)
    
    # สถานการณ์ที่ 5: นาฬิกาปลุก
    print("Scenario 5: Alarm clock pattern")
    bz.alarm_sequence(stages=5, base_freq_ms=100, increment_ms=100, repeat=3)
    
    print("✅ Practical applications demo complete\n")


async def main():
    """รันการสาธิตทั้งหมด"""
    print("=" * 60)
    print("Buzzer Patterns & Advanced Features Demo")
    print("=" * 60)
    
    try:
        await demo_active_buzzer_patterns()
        await demo_passive_buzzer_advanced()
        await demo_practical_applications()
        
        print("\n" + "=" * 60)
        print("🎉 All demos completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
