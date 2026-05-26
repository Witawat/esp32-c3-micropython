"""
ตัวอย่างการใช้งาน Button ขั้นสูง

สาธิตการใช้งาน:
- Long press detection (กดค้าง)
- Multi-click detection (ดับเบิลคลิก, ทริปเปิลคลิก)
- Press duration tracking (วัดระยะเวลาการกด)
- Pattern recognition (จดจำรูปแบบการกด)
"""

import sys
sys.path.insert(0, '/lib')

from input.button import Button, PressPattern
import asyncio
import time


def demo_basic_button():
    """สาธิตการใช้งานพื้นฐาน"""
    print("\n🔘 === Basic Button Demo ===")
    
    # สร้างปุ่มที่ GPIO 9 (pull-up, active low)
    btn = Button(pin=9, pull='up', debounce_ms=50)
    
    # ตรวจสอบสถานะการกด
    print("Press the button to test...")
    for i in range(5):
        if btn.is_pressed:
            print(f"  Button is pressed! (check {i+1}/5)")
            break
        time.sleep_ms(100)
    
    print("✅ Basic demo complete\n")


def demo_long_press():
    """สาธิต Long Press Detection"""
    print("\n⏱️  === Long Press Detection Demo ===")
    
    btn = Button(pin=9, pull='up', long_press_threshold_ms=1000)
    
    # ตัวอย่างที่ 1: ตั้งค่า callback สำหรับ long press
    def on_long_press_handler(duration_ms):
        print(f"  🔥 Long press detected! Held for {duration_ms}ms")
    
    btn.on_long_press(on_long_press_handler, threshold_ms=1000)
    
    # ตัวอย่างที่ 2: ใช้กับ press/release callbacks ปกติ
    def on_press():
        print("  Button pressed")
    
    def on_release():
        duration = btn.get_last_press_duration()
        print(f"  Button released (pressed for {duration}ms)")
    
    btn.on_press(on_press)
    btn.on_release(on_release)
    
    print("Instructions:")
    print("  - Quick press (< 1s): Will show press/release with duration")
    print("  - Long press (> 1s): Will trigger long press callback")
    print("  - Try pressing for different durations!")
    print("\nTesting for 10 seconds...")
    
    # รอให้ผู้ใช้ทดสอบ (ในสถานการณ์จริงจะรันใน loop หลัก)
    time.sleep_ms(10000)
    
    print("✅ Long press demo complete\n")


def demo_multi_click():
    """สาธิต Multi-Click Detection"""
    print("\n👆 === Multi-Click Detection Demo ===")
    
    btn = Button(pin=9, pull='up', click_window_ms=300, max_clicks=5)
    
    # ตัวอย่างที่ 1: ดับเบิลคลิก
    def on_double_click(count):
        print(f"  ✨ Double click detected! ({count} clicks)")
    
    btn.on_double_click(on_double_click)
    
    # ตัวอย่างที่ 2: ทริปเปิลคลิก
    def on_triple_click(count):
        print(f"  🌟 Triple click detected! ({count} clicks)")
    
    btn.on_triple_click(on_triple_click)
    
    # ตัวอย่างที่ 3: Generic multi-click handler
    def on_multi_click_handler(count):
        print(f"  🎯 Multi-click: {count} clicks detected!")
    
    btn.on_multi_click(4, on_multi_click_handler)  # 4 clicks
    btn.on_multi_click(5, on_multi_click_handler)  # 5 clicks
    
    print("Instructions:")
    print("  - Double click (2 quick presses): Triggers double click")
    print("  - Triple click (3 quick presses): Triggers triple click")
    print("  - Quad click (4 quick presses): Triggers 4-click handler")
    print("  - Quintuple click (5 quick presses): Triggers 5-click handler")
    print(f"  - Click window: {btn._click_window_ms}ms between clicks")
    print("\nTesting for 15 seconds...")
    
    time.sleep_ms(15000)
    
    print("✅ Multi-click demo complete\n")


async def demo_async_watch():
    """สาธิต Async Watch พร้อม long press detection"""
    print("\n⚡ === Async Watch Demo ===")
    
    btn = Button(pin=9, pull='up', long_press_threshold_ms=1500)
    
    async def handle_press():
        print("  [Async] Button pressed")
    
    async def handle_release(duration=None, is_long_press=False):
        if is_long_press:
            print(f"  [Async] Long press released after {duration}ms")
        else:
            dur = btn.get_last_press_duration()
            print(f"  [Async] Button released (duration: {dur}ms)")
    
    print("Instructions:")
    print("  - Press and release quickly: Shows normal press/release")
    print("  - Hold for > 1.5 seconds: Triggers long press detection")
    print("\nWatching for 10 seconds...")
    
    # รัน watch task
    watch_task = asyncio.create_task(btn.watch(
        interval_ms=30,
        on_press=handle_press,
        on_release=handle_release
    ))
    
    await asyncio.sleep(10)
    watch_task.cancel()
    
    print("✅ Async watch demo complete\n")


def demo_pattern_recognition():
    """สาธิต Pattern Recognition Engine"""
    print("\n🧩 === Pattern Recognition Demo ===")
    
    btn = Button(pin=9, pull='up')
    
    # ตัวอย่างที่ 1: รูปแบบ SOS (สั้น-สั้น-สั้น ยาว-ยาว-ยาว สั้น-สั้น-สั้น)
    # แต่ในรูปแบบง่าย: สั้น-สั้น-ยาว
    sos_pattern = PressPattern([
        (50, 250),    # กดครั้งที่ 1: 50-250ms (สั้น)
        (50, 250),    # กดครั้งที่ 2: 50-250ms (สั้น)
        (400, 1000)   # กดครั้งที่ 3: 400-1000ms (ยาว)
    ], max_gap_ms=500)
    
    def on_sos_detected(pattern_name):
        print(f"  🆘 SOS pattern detected: '{pattern_name}'")
    
    btn.register_pattern("sos", sos_pattern, on_sos_detected)
    
    # ตัวอย่างที่ 2: รูปแบบ "quick-double" (กดเร็ว 2 ครั้ง)
    quick_double = PressPattern([
        (30, 150),   # กดครั้งแรก: สั้นมาก
        (30, 150)    # กดครั้งที่สอง: สั้นมาก
    ], max_gap_ms=300)
    
    def on_quick_double(pattern_name):
        print(f"  ⚡ Quick double pattern: '{pattern_name}'")
    
    btn.register_pattern("quick-double", quick_double, on_quick_double)
    
    # ตัวอย่างที่ 3: รูปแบบ "hold-release-hold"
    hold_pattern = PressPattern([
        (500, 2000),  # กดค้างยาว
        (500, 2000)   # กดค้างยาวอีกครั้ง
    ], max_gap_ms=1000)
    
    def on_hold_pattern(pattern_name):
        print(f"  🎯 Hold pattern detected: '{pattern_name}'")
    
    btn.register_pattern("double-hold", hold_pattern, on_hold_pattern)
    
    print("Registered patterns:")
    for name in btn._registered_patterns.keys():
        print(f"  - {name}")
    
    print("\nInstructions:")
    print("  - SOS pattern: Short-Short-Long (press durations: ~100ms, ~100ms, ~600ms)")
    print("  - Quick double: Two very quick presses (~80ms each, within 300ms)")
    print("  - Double hold: Two long presses (~1s each, within 1s gap)")
    print("\nTesting for 20 seconds...")
    
    time.sleep_ms(20000)
    
    # ล้าง patterns
    btn.clear_patterns()
    
    print("✅ Pattern recognition demo complete\n")


def demo_duration_tracking():
    """สาธิต Press Duration Tracking"""
    print("\n📏 === Press Duration Tracking Demo ===")
    
    btn = Button(pin=9, pull='up')
    
    def on_release_with_duration():
        duration = btn.get_last_press_duration()
        
        # จำแนกประเภทตามระยะเวลา
        if duration < 200:
            category = "Quick tap"
        elif duration < 500:
            category = "Normal press"
        elif duration < 1000:
            category = "Medium hold"
        else:
            category = "Long hold"
        
        print(f"  {category}: {duration}ms")
    
    btn.on_release(on_release_with_duration)
    
    print("Instructions:")
    print("  - Quick tap (< 200ms): Categorized as 'Quick tap'")
    print("  - Normal press (200-500ms): Categorized as 'Normal press'")
    print("  - Medium hold (500-1000ms): Categorized as 'Medium hold'")
    print("  - Long hold (> 1000ms): Categorized as 'Long hold'")
    print("\nTesting for 10 seconds...")
    
    time.sleep_ms(10000)
    
    print("✅ Duration tracking demo complete\n")


async def demo_combined_features():
    """สาธิตการใช้ฟีเจอร์ร่วมกัน"""
    print("\n🎪 === Combined Features Demo ===")
    
    btn = Button(
        pin=9, 
        pull='up',
        long_press_threshold_ms=1000,
        click_window_ms=300,
        max_clicks=3
    )
    
    # ตั้งค่า handlers หลายแบบพร้อมกัน
    def on_press():
        print("  [Event] Pressed")
    
    def on_release():
        duration = btn.get_last_press_duration()
        print(f"  [Event] Released ({duration}ms)")
    
    def on_long_press(duration):
        print(f"  [Event] Long press: {duration}ms")
    
    def on_double_click(count):
        print(f"  [Event] Double click!")
    
    def on_triple_click(count):
        print(f"  [Event] Triple click!")
    
    btn.on_press(on_press)
    btn.on_release(on_release)
    btn.on_long_press(on_long_press)
    btn.on_double_click(on_double_click)
    btn.on_triple_click(on_triple_click)
    
    print("All features enabled simultaneously:")
    print("  ✓ Press/Release detection")
    print("  ✓ Long press (> 1s)")
    print("  ✓ Double click")
    print("  ✓ Triple click")
    print("  ✓ Duration tracking")
    print("\nTry different interactions for 15 seconds...")
    
    time.sleep_ms(15000)
    
    print("✅ Combined features demo complete\n")


async def main():
    """รันการสาธิตทั้งหมด"""
    print("=" * 60)
    print("Button Advanced Features Demo")
    print("=" * 60)
    
    try:
        # การสาธิตแบบ synchronous
        demo_basic_button()
        demo_long_press()
        demo_multi_click()
        demo_pattern_recognition()
        demo_duration_tracking()
        
        # การสาธิตแบบ asynchronous
        await demo_async_watch()
        await demo_combined_features()
        
        print("\n" + "=" * 60)
        print("🎉 All demos completed successfully!")
        print("=" * 60)
        print("\n💡 Tips:")
        print("  - Adjust thresholds based on your use case")
        print("  - Combine features for rich user interactions")
        print("  - Use pattern recognition for complex gestures")
        print("  - Monitor duration for context-aware responses")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
