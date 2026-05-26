# I/O Expander Drivers — Remote GPIO & PWM

> **Interface**: I2C expanders  
> **รองรับ**: ESP32 ทุกรุ่น  

---

## การเชื่อมต่อ

```
ESP32-C3          I/O Expander
─────────         ─────────────
SDA (GPIO21) ───  SDA
SCL (GPIO22) ───  SCL
3.3V         ──→  VCC
GND          ───  GND
A0/A1/A2     ───  GND/VCC (ตั้ง Address)
```

---

## 🟢 Basic Usage

```python
from i2c import I2CDriver
from io_expander import PCF8574, MCP23017, PCA9685

i2c = I2CDriver(sda=21, scl=22)

# ── PCF8574 (8-bit, LCD backpack) ──
pcf = PCF8574(i2c.bus, address=0x27)
pcf.set_bit(0, True)   # P0 = HIGH
pcf.set_bit(7, False)  # P7 = LOW
print(pcf.get_bit(3))  # read P3

# ── MCP23017 (16-bit with interrupt) ──
mcp = MCP23017(i2c.bus)
mcp.set_pin_mode(0, 'output')
mcp.write_pin(0, True)
val = mcp.read_pin(8)  # read GPB0

# ── PCA9685 (16-ch PWM, servo) ──
pwm = PCA9685(i2c.bus)
pwm.set_freq(50)       # 50Hz for servo
pwm.set_duty(0, 7.5)   # ch0 = 7.5% (center)
```

---

## 🟡 Intermediate Usage

```python
# ── PCF8574 byte-level ──
pcf.write_byte(0xAA)  # all pins = 10101010
state = pcf.read_byte()

# ── MCP23017 port-level ──
mcp.write_port_a(0xFF)   # PORTA all HIGH
mcp.write_port_b(0x00)   # PORTB all LOW
pa = mcp.read_port_a()
pb = mcp.read_port_b()

# ── PCA9685 servo control ──
pwm.set_freq(50)
pwm.set_pulse_us(0, 1500)   # center (1500µs)
pwm.set_pulse_us(1, 500)    # left (500µs)
pwm.set_pulse_us(2, 2500)   # right (2500µs)
```

---

## 🔴 Advanced Usage

```python
# ── MCP23017 interrupt ──
mcp.set_pin_mode(0, 'input')
mcp.enable_interrupt(0, True)
intfa, intfb = mcp.get_interrupt_flags()
if intfa:
    cap_a, cap_b = mcp.get_interrupt_capture()
    print(f"Interrupt! PORTA=0x{cap_a:02X}")

# ── PCA9685 servo array ──
pwm = PCA9685(i2c.bus)
pwm.set_freq(50)

# Control 4 servos
servos = {
    'base': 0,
    'shoulder': 1,
    'elbow': 2,
    'gripper': 3,
}

def set_servo_angle(channel: int, angle: float):
    """0°=center, ±90° range"""
    us = 1500 + angle * 1000 / 90
    pwm.set_pulse_us(channel, us)

set_servo_angle(servos['base'], 45)

# ── LED strip via PCA9685 ──
pwm.set_freq(1000)  # 1kHz for LEDs
for ch in range(16):
    pwm.set_duty(ch, 50)  # 50% brightness

pwm.all_off()
pwm.deinit()
```

---

## API Reference

### `PCF8574` (8-bit I/O)

| Method | Description |
|---|---|
| `write_byte(value)` | เขียน 8 pins |
| `read_byte()` | อ่าน 8 pins |
| `set_bit(bit, value)` | Set 1 pin |
| `get_bit(bit)` | Read 1 pin |
| `toggle_bit(bit)` | Toggle 1 pin |
| `set_mask(mask, value)` | Write masked bits |
| `pulse_bit(bit, ms)` | Short pulse |

### `MCP23017` (16-bit I/O + Interrupt)

| Method | Description |
|---|---|
| `set_pin_mode(pin, mode, pull_up)` | Input/output |
| `write_pin(pin, value)` | Write 1 pin |
| `read_pin(pin)` | Read 1 pin |
| `write_port_a/b(value)` | Write 8-bit port |
| `read_port_a/b()` | Read 8-bit port |
| `write_all(value)` | Write 16-bit |
| `read_all()` | Read 16-bit |
| `enable_interrupt(pin)` | Enable interrupt |
| `get_interrupt_flags()` | Read flags |
| `get_interrupt_capture()` | Read captured values |

### `PCA9685` (16-ch PWM)

| Method | Description |
|---|---|
| `set_freq(freq)` | Set PWM frequency |
| `set_pwm(ch, on, off)` | Raw 12-bit PWM |
| `set_duty(ch, pct)` | Duty 0–100% |
| `set_pulse_us(ch, us)` | Pulse in µs |
| `all_off()` | All channels off |
| `all_on()` | All channels 100% |
| `reset()` | Software reset |
| `deinit()` | Sleep mode |

---

## Address Reference

| Chip | Base Address | Range |
|---|---|---|
| PCF8574 | 0x20 | 0x20–0x27 |
| PCF8574A | 0x38 | 0x38–0x3F |
| MCP23017 | 0x20 | 0x20–0x27 |
| PCA9685 | 0x40 | 0x40–0x7F |
