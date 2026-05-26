# Timer Helper — Periodic & One-Shot Callbacks

> **Interface**: `machine.Timer` + software fallback  
> **รองรับ**: ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6  

---

## 🟢 Basic Usage

```python
from timer import TimerHelper, WatchTimer

# ── Periodic timer ──
t = TimerHelper()
t.set_interval(lambda: print("Tick every second!"), period_ms=1000)

# ── One-shot timer ──
t.set_timeout(lambda: print("Boom after 5s!"), delay_ms=5000)

# ── Watch timer (elapsed tracking) ──
wt = WatchTimer()
wt.start()
# ... do work ...
print(f"Elapsed: {wt.elapsed_ms}ms")

t.stop_all()
```

---

## 🟡 Intermediate Usage

```python
from timer import TimerHelper, WatchTimer

t = TimerHelper()

# ── Cancellable timer ──
cid = t.set_interval(lambda: print("tick"), period_ms=500)
# ... later ...
t.cancel(cid)  # stop this specific timer

# ── Watch timer for timeout ──
wt = WatchTimer()
wt.start()

while not wt.has_elapsed(10000):  # 10s timeout
    if some_condition:
        print("Success!")
        break
else:
    print("Timeout!")

# ── Debounce pattern ──
debounce = WatchTimer()
last_press = 0

def on_press():
    if debounce.has_elapsed(200):  # 200ms debounce
        print("Valid press!")
        debounce.reset()

# ── Multiple timers ──
t1 = TimerHelper(timer_id=0)
t2 = TimerHelper(timer_id=1)

t1.set_interval(heartbeat, period_ms=1000)
t2.set_timeout(shutdown, delay_ms=300000)  # 5 minutes
```

---

## 🔴 Advanced Usage

```python
from timer import TimerHelper, WatchTimer
import asyncio

# ── Heartbeat + timeout watchdog ──
class Watchdog:
    def __init__(self, timeout_ms: int = 5000):
        self.timeout_ms = timeout_ms
        self._timer = WatchTimer()
        self._timer.start()
    
    def feed(self):
        """Feed the watchdog — reset timer"""
        self._timer.reset()
    
    def is_expired(self) -> bool:
        return self._timer.has_elapsed(self.timeout_ms)

# ── Async repeated task ──
t = TimerHelper()

async def sensor_poll():
    """Poll sensor every 2s"""
    print("Reading sensor...")
    # read sensor here

t.set_interval(lambda: asyncio.create_task(sensor_poll()), period_ms=2000)

# ── Performance profiling ──
prof = WatchTimer()
prof.start()
# ... heavy computation ...
print(f"Took {prof.elapsed_ms}ms ({prof.elapsed_sec}s)")

# Cleanup
t.deinit()
```

---

## API Reference

### `TimerHelper`

| Method | Description |
|---|---|
| `__init__(timer_id)` | Create timer (None=auto) |
| `set_interval(callback, period_ms)` → id | Periodic callback |
| `set_timeout(callback, delay_ms)` → id | One-shot callback |
| `cancel(callback_id)` | Cancel specific callback |
| `stop_all()` | Stop all callbacks |
| `deinit()` | Cleanup |

### `WatchTimer` (Software)

| Method | Description |
|---|---|
| `start()` / `reset()` | Start/reset timer |
| `stop()` | Stop timer |
| `elapsed_ms` → int | Elapsed ms |
| `elapsed_sec` → float | Elapsed seconds |
| `has_elapsed(duration_ms)` → bool | Check timeout |
| `remaining_ms(duration_ms)` → int | Remaining ms |

---

## ESP32-C3 Specific

| Item | Value |
|---|---|
| Hardware timers | 4 (Timer0–Timer3) |
| Auto-allocate | ✅ Round-robin across 4 timers |
| Software fallback | ✅ Auto when HW timer fails |
| Timer resolution | ~1 µs |
| Max period | ~134 seconds per hardware timer |
