# Digital I/O — Pin Helpers

> **Interface**: `machine.Pin` helpers  
> **รองรับ**: ESP32 ทุกรุ่น  

---

## การเชื่อมต่อ

### DigitalInput (Button)
```
ESP32-C3          Button
─────────         ──────
GPIOx  ─────────  Terminal 1
GND    ─────────  Terminal 2 (ผ่าน internal PULL_UP)
```

### DigitalOutput (LED)
```
ESP32-C3          LED
─────────         ───
GPIOx  ──[220Ω]── LED+
GND    ─────────  LED-
```

---

## 🟢 Basic Usage

```python
from pin import DigitalInput, DigitalOutput

# ── Input ──
btn = DigitalInput(pin=5, pull='up')
print(btn.value)         # 0 or 1

if btn.is_pressed():     # LOW when pull-up
    print("Pressed!")

# ── Output ──
led = DigitalOutput(pin=2)
led.on()
led.off()
led.toggle()
led.pulse(500)  # 500ms on then off

led.deinit()
btn.deinit()
```

---

## 🟡 Intermediate Usage

```python
from pin import DigitalInput, DigitalOutput

# ── Debounced input ──
btn = DigitalInput(pin=5, pull='up')
btn.debounce_ms = 50  # 50ms debounce

while True:
    if btn.is_pressed():
        print("Stable press!")

# ── Active LOW output (relay) ──
relay = DigitalOutput(pin=16, active_low=True)
relay.on()   # GPIO=0 → relay ON
relay.off()  # GPIO=1 → relay OFF

# ── Wait for edge ──
btn = DigitalInput(pin=5, pull='up')
if btn.wait_for_edge(btn.IRQ_FALLING, timeout_ms=5000):
    print("Button pressed within 5s!")
else:
    print("Timeout — no press detected")

# ── With interrupt ──
def on_press(pin):
    print(f"GPIO{pin} changed!")

btn.irq(on_press, trigger=DigitalInput.IRQ_FALLING)
```

---

## 🔴 Advanced Usage

```python
from pin import DigitalInput, DigitalOutput
import asyncio

# ── Multi-button monitoring ──
buttons = {
    'up': DigitalInput(pin=5, pull='up'),
    'down': DigitalInput(pin=6, pull='up'),
    'select': DigitalInput(pin=7, pull='up'),
}

async def monitor_buttons():
    while True:
        for name, btn in buttons.items():
            if btn.is_pressed():
                print(f"🟢 {name} pressed!")
        await asyncio.sleep_ms(50)

# ── LED sequence ──
led = DigitalOutput(pin=2)

async def blink(count: int, on_ms: int = 200, off_ms: int = 200):
    for _ in range(count):
        led.on()
        await asyncio.sleep_ms(on_ms)
        led.off()
        await asyncio.sleep_ms(off_ms)

# ── Edge-triggered state machine ──
btn = DigitalInput(pin=5, pull='up')

async def wait_press(btn: DigitalInput, timeout_ms: int = 0):
    """Async wait for press"""
    import time
    start = time.ticks_ms()
    while timeout_ms == 0 or time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
        if btn.is_pressed():
            return True
        await asyncio.sleep_ms(10)
    return False
```

---

## API Reference

### `DigitalInput`

| Method | Description |
|---|---|
| `__init__(pin, pull, invert)` | สร้าง input pin |
| `value` → int | อ่านค่า (0/1) พร้อม debounce |
| `is_pressed()` → bool | ตรวจสอบว่ากด |
| `is_released()` → bool | ตรวจสอบว่าปล่อย |
| `is_high()` / `is_low()` | Check level |
| `irq(handler, trigger)` | ตั้ง interrupt |
| `disable_irq()` | ปิด interrupt |
| `wait_for_edge(edge, timeout)` | Blocking wait for edge |
| `debounce_ms` (property) | Get/set debounce |
| `deinit()` | Cleanup |

### `DigitalOutput`

| Method | Description |
|---|---|
| `__init__(pin, active_low, initial_state)` | สร้าง output pin |
| `on()` / `off()` | Set state |
| `toggle()` | Toggle state |
| `set(state)` | Set explicit state |
| `pulse(duration_ms)` | Short pulse (blocking) |
| `value` / `is_on` | Check state |
| `deinit()` | Cleanup |

---

## ESP32-C3 Specific

| Item | Value |
|---|---|
| All GPIOs | ✅ Digital I/O capable |
| PULL_UP | ✅ ~45kΩ internal |
| PULL_DOWN | ✅ ~45kΩ internal |
| Interrupts | ✅ RISING, FALLING, BOTH |
| Max input V | 3.3V (not 5V tolerant!) |
