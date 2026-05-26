"""
ตัวอย่างการใช้งาน System Utilities — Timer Helper & RTC
แสดงวิธีใช้งาน Timer (periodic/one-shot), WatchTimer, และ RTC Factory

ไม่ต้องใช้ฮาร์ดแวร์เพิ่ม — ทำงานบน ESP32-C3 ได้เลย
"""

import sys
sys.path.append('/lib')

import asyncio
import time


# ============================================================
# 1. Timer — Periodic Callback (set_interval)
# ============================================================
async def example_timer_interval():
    """Periodic timer — callback ทุก 500ms"""
    print("\n" + "=" * 50)
    print("Timer — Periodic Callback (500ms)")
    print("=" * 50)

    from timer import TimerHelper

    counter = [0]  # use list for mutability

    def tick():
        counter[0] += 1
        print(f"  ⏰ Tick #{counter[0]}")

    t = TimerHelper()
    tid = t.set_interval(tick, period_ms=500)

    # Let it run for 2 seconds
    await asyncio.sleep_ms(2200)

    t.cancel(tid)
    t.deinit()
    print(f"✅ Timer Interval OK ({counter[0]} ticks)")


# ============================================================
# 2. Timer — One-Shot Callback (set_timeout)
# ============================================================
async def example_timer_timeout():
    """One-shot timer — callback หลังจาก delay"""
    print("\n" + "=" * 50)
    print("Timer — One-Shot (2s delay)")
    print("=" * 50)

    from timer import TimerHelper

    def on_timeout():
        print("💥 Timeout! 2 seconds elapsed")

    t = TimerHelper()
    tid = t.set_timeout(on_timeout, delay_ms=2000)

    print("Waiting...")
    await asyncio.sleep_ms(2500)

    t.deinit()
    print("✅ Timer Timeout OK")


# ============================================================
# 3. WatchTimer — Elapsed Time Tracking
# ============================================================
async def example_watch_timer():
    """Software WatchTimer — วัด elapsed time"""
    print("\n" + "=" * 50)
    print("WatchTimer — Elapsed Tracking")
    print("=" * 50)

    from timer import WatchTimer

    wt = WatchTimer()
    wt.start()

    # Simulate work
    await asyncio.sleep_ms(150)

    print(f"Elapsed: {wt.elapsed_ms}ms ({wt.elapsed_sec:.3f}s)")

    # Timeout check
    if wt.has_elapsed(100):
        print("✅ 100ms elapsed")
    if not wt.has_elapsed(500):
        print("ℹ️  < 500ms")

    # Remaining time
    remaining = wt.remaining_ms(500)
    print(f"Remaining to 500ms: {remaining}ms")

    # Reset
    wt.reset()
    await asyncio.sleep_ms(50)
    print(f"After reset: {wt.elapsed_ms}ms")

    wt.stop()
    print("✅ WatchTimer OK")


# ============================================================
# 4. WatchTimer — Debounce Pattern
# ============================================================
async def example_debounce():
    """WatchTimer used for button debounce"""
    print("\n" + "=" * 50)
    print("WatchTimer — Debounce Pattern")
    print("=" * 50)

    from timer import WatchTimer
    from pin import DigitalInput

    btn = DigitalInput(pin=5, pull='up')
    debounce = WatchTimer()
    debounce.start()

    press_count = 0
    last_state = False

    print("Press button for 3 seconds (with 200ms debounce)...")
    start = time.ticks_ms()

    while time.ticks_diff(time.ticks_ms(), start) < 3000:
        current = btn.is_pressed()

        if current and not last_state:  # rising edge (press)
            if debounce.has_elapsed(200):  # 200ms since last press
                press_count += 1
                print(f"  ✅ Valid press #{press_count}")
                debounce.reset()

        last_state = current
        await asyncio.sleep_ms(10)

    print(f"Total valid presses: {press_count}")
    debounce.stop()
    btn.deinit()
    print("✅ Debounce Pattern OK")


# ============================================================
# 5. Timer — Performance Measurement
# ============================================================
async def example_timer_perf():
    """Timer for performance profiling"""
    print("\n" + "=" * 50)
    print("WatchTimer — Performance Profiling")
    print("=" * 50)

    from timer import WatchTimer

    prof = WatchTimer()
    prof.start()

    # Simulate heavy computation
    total = 0
    for i in range(1000):
        total += i * i

    elapsed_us = prof.elapsed_ms * 1000
    print(f"Loop 1000 iterations: {prof.elapsed_ms}ms ({elapsed_us}µs)")
    print(f"Average per iteration: {elapsed_us / 1000:.1f}µs")

    prof.stop()
    print("✅ Performance OK")


# ============================================================
# 6. RTC — Factory Pattern (Auto-Detect DS3231)
# ============================================================
async def example_rtc_factory():
    """RTC with auto-detection of DS3231"""
    print("\n" + "=" * 50)
    print("RTC — Factory Pattern (Auto-Detect)")
    print("=" * 50)

    from system.rtc import RTCFactory, RTCManager

    # Auto-detect: DS3231 if available, else machine.RTC
    rtc = RTCFactory.create(sda=21, scl=22)

    # Read current time
    dt = rtc.get_datetime()
    if dt:
        y, m, d, wd, h, mi, s, _ = dt
        print(f"Current time: {y}-{m:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}")

    # Manual set (if time is wrong)
    # rtc.set_datetime((2026, 5, 2, 6, 12, 0, 0, 0))

    print("✅ RTC Factory OK")


# ============================================================
# 7. RTC — NTP Sync
# ============================================================
async def example_rtc_ntp():
    """NTP time sync (ต้องต่อ WiFi ก่อน)"""
    print("\n" + "=" * 50)
    print("RTC — NTP Time Sync")
    print("=" * 50)

    from system.rtc import RTCFactory, NTPTimeSync

    rtc = RTCFactory.create_default()
    ntp = NTPTimeSync(rtc, timezone_offset=7)  # ICT/Bangkok

    # Try to sync (needs WiFi!)
    try:
        from wifi.wifimanager import WiFiManager
        wifi = WiFiManager()
        await wifi.connect()

        if ntp.sync():
            dt = rtc.get_datetime()
            y, m, d, wd, h, mi, s, _ = dt
            print(f"✅ Synced: {y}-{m:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d} (UTC+7)")
        else:
            print("⚠️ NTP sync failed — check WiFi")
    except Exception as e:
        print(f"ℹ️  NTP sync not attempted: {e}")
        print("   (ต้องต่อ WiFi ก่อนใช้งาน NTP)")

    print("✅ RTC NTP OK")


# ============================================================
# 8. RTC — Backup to DS3231
# ============================================================
async def example_rtc_backup():
    """Backup machine.RTC to DS3231 (battery-backed)"""
    print("\n" + "=" * 50)
    print("RTC — Backup/Restore to DS3231")
    print("=" * 50)

    from system.rtc import RTCFactory

    rtc = RTCFactory.create(sda=21, scl=22)

    # Show current time
    dt = rtc.get_datetime()
    if dt:
        y, m, d, wd, h, mi, s, _ = dt
        print(f"Before sync: {y}-{m:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}")

    # If external DS3231 is attached, sync from it
    if rtc._external_rtc:
        rtc.sync_from_ds3231(rtc._external_rtc)
        dt = rtc.get_datetime()
        y, m, d, wd, h, mi, s, _ = dt
        print(f"✅ Restored from DS3231: {y}-{m:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}")
    else:
        print("ℹ️  No external DS3231 — using machine.RTC only")

    print("✅ RTC Backup OK")


# ============================================================
# Main
# ============================================================
async def main():
    print("=" * 50)
    print("System Utilities — Timer & RTC Examples")
    print("=" * 50)

    # Timer
    await example_timer_interval()
    await example_timer_timeout()
    await example_watch_timer()
    await example_debounce()
    await example_timer_perf()

    # RTC
    await example_rtc_factory()
    await example_rtc_ntp()
    await example_rtc_backup()


asyncio.run(main())
