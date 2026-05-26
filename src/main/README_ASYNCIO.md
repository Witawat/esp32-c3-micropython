# MicroPython asyncio — คู่มือฉบับสมบูรณ์

> เป้าหมาย: ESP32-C3 (MicroPython v1.21+)  
> ครอบคลุมตั้งแต่พื้นฐานจนถึงเทคนิคขั้นสูง

---

## สารบัญ

1. [หลักการทำงานของ Event Loop](#1-หลักการทำงานของ-event-loop)
2. [asyncrun และ asyncsleep](#2-asynciorun-และ-asynciosleep)
3. [Coroutine พื้นฐาน](#3-coroutine-พื้นฐาน)
4. [Task — สร้างและจัดการ](#4-task--สร้างและจัดการ)
5. [gather — รัน coroutine พร้อมกัน](#5-asynciogather--รัน-coroutine-พร้อมกัน)
6. [Event — สื่อสารระหว่าง Task](#6-asyncioevent--สื่อสารระหว่าง-task)
7. [Lock — ป้องกัน Race Condition](#7-asynciolock--ป้องกัน-race-condition)
8. [Queue — ส่งข้อมูลระหว่าง Task](#8-asyncioqueue--ส่งข้อมูลระหว่าง-task)
9. [Timeout และ wait_for](#9-asynciowait_for--timeout)
10. [StreamReader / StreamWriter](#10-asynciostreamreader--streamwriter)
11. [ThreadSafeFlag — interrupt → async](#11-asynciothreadsafeflag--interrupt--async)
12. [Pattern: Producer / Consumer](#12-pattern-producer--consumer)
13. [Pattern: State Machine แบบ async](#13-pattern-state-machine-แบบ-async)
14. [Pattern: Watchdog ด้วย Task](#14-pattern-watchdog-ด้วย-task)
15. [Pattern: Debounce ปุ่มด้วย async](#15-pattern-debounce-ปุ่มด้วย-async)
16. [ข้อควรระวังและ Anti-pattern](#16-ข้อควรระวังและ-anti-pattern)
17. [เปรียบเทียบ asynciosleep vs time.sleep](#17-เปรียบเทียบ-asynciosleep-vs-timesleep)
18. [Memory และ Performance Tips](#18-memory-และ-performance-tips)

---

## 1. หลักการทำงานของ Event Loop

MicroPython ใช้ **cooperative multitasking** — task แต่ละตัว **ต้องยอมสละ CPU** เองโดยใช้ `await`  
Event loop จะวน loop ตรวจว่า task ไหน "พร้อม" แล้วรัน task นั้นต่อ

```
┌─────────────────────────────────────────┐
│              Event Loop                 │
│                                         │
│  Task A ──► await ──► หยุดรอ            │
│                         │               │
│  Task B ◄───────────────┘ ได้รัน        │
│  Task B ──► await ──► หยุดรอ            │
│                         │               │
│  Task A ◄───────────────┘ ได้รัน        │
└─────────────────────────────────────────┘
```

> **กฎสำคัญ**: ถ้า task ใดไม่มี `await` เลย มันจะบล็อก task อื่นทั้งหมด

---

## 2. asyncio.run และ asyncio.sleep

### asyncio.run

```python
import asyncio

async def main():
    print("Hello async!")
    await asyncio.sleep(1)
    print("Done")

asyncio.run(main())  # สร้าง event loop ใหม่และรัน coroutine
```

- ใช้ **ครั้งเดียว** เป็น entry point ของโปรแกรม
- เมื่อ `main()` return event loop จะถูกปิด
- **ห้ามเรียก `asyncio.run()` ซ้อนกัน**

### asyncio.sleep

```python
await asyncio.sleep(1)        # หยุด 1 วินาที (float ได้)
await asyncio.sleep_ms(500)   # หยุด 500 มิลลิวินาที (เร็วกว่า)
await asyncio.sleep(0)        # ยอมสละ CPU 1 รอบ แต่ไม่รอเวลา
```

`await asyncio.sleep(0)` มีประโยชน์มากใน loop ที่ไม่ต้องการรอ แต่ต้องการให้ task อื่นได้ทำงาน

---

## 3. Coroutine พื้นฐาน

```python
import asyncio

# coroutine ธรรมดา
async def say_hello(name: str):
    print(f"Hello {name}")
    await asyncio.sleep(0.5)
    print(f"Bye {name}")

# coroutine ที่ return ค่า
async def add(a: int, b: int) -> int:
    await asyncio.sleep(0)  # ยอมสละ CPU
    return a + b

async def main():
    # เรียกแบบ await — รอให้เสร็จก่อน
    await say_hello("ESP32")

    # รับ return value
    result = await add(3, 4)
    print(f"3 + 4 = {result}")

asyncio.run(main())
```

---

## 4. Task — สร้างและจัดการ

Task คือ coroutine ที่ถูกส่งให้ event loop รัน **โดยไม่ต้อง await ทันที**

### สร้าง Task

```python
import asyncio

async def blink(pin_num: int, interval_ms: int):
    import machine
    led = machine.Pin(pin_num, machine.Pin.OUT)
    while True:
        led.toggle()
        await asyncio.sleep_ms(interval_ms)

async def main():
    # สร้าง task — รันพร้อมกับ main โดยไม่บล็อก
    t1 = asyncio.create_task(blink(8, 500))
    t2 = asyncio.create_task(blink(9, 200))

    await asyncio.sleep(10)  # รอ 10 วินาที

    # ยกเลิก task
    t1.cancel()
    t2.cancel()
    print("Tasks cancelled")

asyncio.run(main())
```

### ตรวจสอบสถานะ Task

```python
async def main():
    task = asyncio.create_task(some_coroutine())

    await asyncio.sleep(1)

    if not task.done():
        print("Task ยังทำงานอยู่")
        task.cancel()
    else:
        print("Task เสร็จแล้ว")
```

### จัดการ CancelledError

```python
async def worker():
    try:
        while True:
            print("working...")
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("Task ถูกยกเลิก — cleanup ที่นี่")
        # ปิด resource, บันทึกข้อมูล ฯลฯ
        raise  # ต้อง re-raise เสมอ
```

---

## 5. asyncio.gather — รัน coroutine พร้อมกัน

`gather` รัน coroutine หลายตัวพร้อมกันและรอให้ **ทุกตัวเสร็จ**

```python
import asyncio

async def task_a():
    await asyncio.sleep(2)
    return "A done"

async def task_b():
    await asyncio.sleep(1)
    return "B done"

async def task_c():
    await asyncio.sleep(3)
    return "C done"

async def main():
    # รันทั้ง 3 พร้อมกัน ใช้เวลารวม ~3 วินาที (ไม่ใช่ 6)
    results = await asyncio.gather(task_a(), task_b(), task_c())
    print(results)  # ['A done', 'B done', 'C done']

asyncio.run(main())
```

> **หมายเหตุ**: MicroPython `gather` อาจไม่รองรับ `return_exceptions=True` ในบางเวอร์ชัน ตรวจสอบก่อนใช้

---

## 6. asyncio.Event — สื่อสารระหว่าง Task

ใช้ส่งสัญญาณ "เหตุการณ์เกิดขึ้นแล้ว" จาก task หนึ่งไปยังอีก task

```python
import asyncio

# ตัวอย่าง: task อ่านเซ็นเซอร์ ส่งสัญญาณให้ task แสดงผล

sensor_ready = asyncio.Event()
sensor_value = 0

async def sensor_reader():
    global sensor_value
    while True:
        await asyncio.sleep(2)
        sensor_value = 42  # อ่านค่าจริงจากเซ็นเซอร์
        sensor_ready.set()   # แจ้ง task อื่น

async def display_task():
    while True:
        await sensor_ready.wait()  # บล็อกจนกว่า event จะถูก set
        sensor_ready.clear()       # reset event สำหรับรอบถัดไป
        print(f"Sensor: {sensor_value}")

async def main():
    asyncio.create_task(sensor_reader())
    asyncio.create_task(display_task())
    await asyncio.sleep(20)

asyncio.run(main())
```

---

## 7. asyncio.Lock — ป้องกัน Race Condition

ใช้เมื่อหลาย task เข้าถึง **shared resource** เดียวกัน เช่น UART, SPI, I2C

```python
import asyncio

i2c_lock = asyncio.Lock()

async def read_sensor_a(i2c):
    async with i2c_lock:  # รอให้ได้ lock ก่อน
        # ส่วนนี้รัน exclusive — task อื่นต้องรอ
        result = i2c.readfrom(0x48, 2)
        await asyncio.sleep_ms(10)
    return result

async def read_sensor_b(i2c):
    async with i2c_lock:
        result = i2c.readfrom(0x76, 6)
        await asyncio.sleep_ms(20)
    return result

async def main():
    import machine
    i2c = machine.SoftI2C(scl=machine.Pin(5), sda=machine.Pin(4))
    # ทั้งสอง task รันพร้อมกัน แต่ Lock ป้องกัน I2C clash
    await asyncio.gather(read_sensor_a(i2c), read_sensor_b(i2c))

asyncio.run(main())
```

---

## 8. asyncio.Queue — ส่งข้อมูลระหว่าง Task

Queue ปลอดภัยสำหรับการส่งข้อมูลระหว่าง task โดยไม่ต้องใช้ global variable

```python
import asyncio

async def producer(queue: asyncio.Queue):
    """อ่านข้อมูลและใส่ queue"""
    count = 0
    while True:
        data = {"id": count, "value": count * 10}
        await queue.put(data)
        print(f"[Producer] ส่ง: {data}")
        count += 1
        await asyncio.sleep(1)

async def consumer(queue: asyncio.Queue):
    """รับข้อมูลจาก queue และประมวลผล"""
    while True:
        data = await queue.get()  # บล็อกจนมีข้อมูล
        print(f"[Consumer] รับ: {data}")
        await asyncio.sleep(2)   # ประมวลผลช้ากว่า producer

async def main():
    q = asyncio.Queue(maxsize=10)  # buffer 10 รายการ
    asyncio.create_task(producer(q))
    asyncio.create_task(consumer(q))
    await asyncio.sleep(30)

asyncio.run(main())
```

### Queue แบบ non-blocking

```python
# ใส่โดยไม่รอ (raise QueueFull ถ้าเต็ม)
try:
    queue.put_nowait(data)
except asyncio.QueueFull:
    print("Queue เต็ม ทิ้งข้อมูล")

# รับโดยไม่รอ (raise QueueEmpty ถ้าว่าง)
try:
    data = queue.get_nowait()
except asyncio.QueueEmpty:
    pass
```

---

## 9. asyncio.wait_for — Timeout

ใช้กำหนด timeout ให้ coroutine เพื่อไม่ให้รอนานเกินไป

```python
import asyncio

async def slow_operation():
    await asyncio.sleep(10)
    return "done"

async def main():
    try:
        # ถ้าไม่เสร็จใน 3 วินาที raise TimeoutError
        result = await asyncio.wait_for(slow_operation(), timeout=3)
    except asyncio.TimeoutError:
        print("Timeout! ดำเนินการต่อ...")

asyncio.run(main())
```

### ตัวอย่างจริง: HTTP request with timeout

```python
async def fetch_with_timeout(url: str, timeout_s: int = 5):
    try:
        response = await asyncio.wait_for(
            http_get(url),
            timeout=timeout_s
        )
        return response
    except asyncio.TimeoutError:
        print(f"[HTTP] Timeout หลัง {timeout_s}s")
        return None
```

---

## 10. asyncio.StreamReader / StreamWriter

ใช้กับ UART, TCP Socket แบบ async ไม่บล็อก

### UART แบบ async

```python
import asyncio
from machine import UART

async def uart_reader(reader: asyncio.StreamReader):
    while True:
        line = await reader.readline()  # รอบรรทัดใหม่
        print(f"[UART RX] {line.decode().strip()}")

async def uart_writer(writer: asyncio.StreamWriter):
    count = 0
    while True:
        msg = f"Hello {count}\r\n"
        writer.write(msg.encode())
        await writer.drain()  # รอให้ส่งข้อมูลออกจริงๆ
        count += 1
        await asyncio.sleep(2)

async def main():
    uart = UART(1, baudrate=115200, tx=21, rx=20)
    reader = asyncio.StreamReader(uart)
    writer = asyncio.StreamWriter(uart, {})

    asyncio.create_task(uart_reader(reader))
    asyncio.create_task(uart_writer(writer))
    await asyncio.sleep(60)

asyncio.run(main())
```

### TCP Server แบบ async

```python
import asyncio
import network

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"[TCP] Client: {addr}")

    try:
        while True:
            data = await asyncio.wait_for(reader.read(256), timeout=30)
            if not data:
                break
            print(f"[TCP] Received: {data}")
            writer.write(b"OK\r\n")
            await writer.drain()
    except asyncio.TimeoutError:
        print("[TCP] Client timeout")
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 8080)
    print("[TCP] Server started on port 8080")
    async with server:
        await server.serve_forever()

asyncio.run(main())
```

---

## 11. asyncio.ThreadSafeFlag — Interrupt → Async

ใช้สื่อสารจาก **ISR (Interrupt Service Routine)** หรือ thread ไปยัง async task  
เพราะ `Event` และ `Queue` ไม่ปลอดภัยใน ISR

```python
import asyncio
from machine import Pin

flag = asyncio.ThreadSafeFlag()

def button_isr(pin):
    flag.set()  # safe ใน ISR

async def button_handler():
    btn = Pin(0, Pin.IN, Pin.PULL_UP)
    btn.irq(trigger=Pin.IRQ_FALLING, handler=button_isr)

    while True:
        await flag.wait()  # รอ ISR set flag
        print("ปุ่มถูกกด!")
        # ทำงานใน async context ปลอดภัย

async def main():
    asyncio.create_task(button_handler())
    await asyncio.sleep(60)

asyncio.run(main())
```

> `ThreadSafeFlag` ต่างจาก `Event` ตรงที่ `set()` ถูกเรียกจาก ISR/thread ได้อย่างปลอดภัย

---

## 12. Pattern: Producer / Consumer

Pattern มาตรฐานสำหรับแยก "การเก็บข้อมูล" กับ "การประมวลผล"

```python
import asyncio
import gc

DATA_QUEUE = asyncio.Queue(maxsize=20)

# ─── Producers ────────────────────────────────────────────
async def sensor_producer(sensor_id: int, interval_ms: int):
    """อ่านเซ็นเซอร์และส่งเข้า queue"""
    while True:
        reading = {"sensor": sensor_id, "val": sensor_id * 100}
        try:
            DATA_QUEUE.put_nowait(reading)
        except asyncio.QueueFull:
            pass  # ทิ้งถ้า queue เต็ม (เลือก policy เอง)
        await asyncio.sleep_ms(interval_ms)

# ─── Consumer ─────────────────────────────────────────────
async def data_processor():
    """ประมวลผลและบันทึกข้อมูล"""
    buffer = []
    while True:
        item = await DATA_QUEUE.get()
        buffer.append(item)

        if len(buffer) >= 5:
            # batch process
            print(f"[Processor] Batch: {buffer}")
            buffer.clear()
            gc.collect()

# ─── Main ─────────────────────────────────────────────────
async def main():
    asyncio.create_task(sensor_producer(1, 500))
    asyncio.create_task(sensor_producer(2, 800))
    asyncio.create_task(data_processor())
    await asyncio.sleep(30)

asyncio.run(main())
```

---

## 13. Pattern: State Machine แบบ async

เหมาะสำหรับ firmware ที่มีหลาย mode เช่น IDLE → CONNECTING → RUNNING → ERROR

```python
import asyncio

class State:
    IDLE       = "IDLE"
    CONNECTING = "CONNECTING"
    RUNNING    = "RUNNING"
    ERROR      = "ERROR"

state = State.IDLE
state_event = asyncio.Event()

async def state_machine():
    global state
    while True:
        if state == State.IDLE:
            print("[SM] IDLE — รอสัญญาณ")
            await state_event.wait()
            state_event.clear()
            state = State.CONNECTING

        elif state == State.CONNECTING:
            print("[SM] CONNECTING...")
            try:
                await asyncio.wait_for(connect_wifi(), timeout=15)
                state = State.RUNNING
            except asyncio.TimeoutError:
                state = State.ERROR

        elif state == State.RUNNING:
            print("[SM] RUNNING")
            await asyncio.sleep(1)
            # ทำงานหลัก

        elif state == State.ERROR:
            print("[SM] ERROR — รอ 5s แล้ว retry")
            await asyncio.sleep(5)
            state = State.IDLE

async def trigger_connect():
    """สั่งให้ state machine เริ่มต้น"""
    global state
    state_event.set()

async def connect_wifi():
    await asyncio.sleep(3)  # จำลองการเชื่อมต่อ

async def main():
    asyncio.create_task(state_machine())
    await asyncio.sleep(1)
    await trigger_connect()
    await asyncio.sleep(30)

asyncio.run(main())
```

---

## 14. Pattern: Watchdog ด้วย Task

ตรวจสอบว่า task หลักยังทำงานปกติ ถ้าไม่ได้ ping ภายในเวลาที่กำหนดให้ reset

```python
import asyncio
import machine

WATCHDOG_TIMEOUT_S = 10
_last_ping = 0

def ping_watchdog():
    """เรียกจาก task หลักเพื่อบอกว่ายังทำงานอยู่"""
    global _last_ping
    import time
    _last_ping = time.time()

async def software_watchdog():
    import time
    global _last_ping
    _last_ping = time.time()

    while True:
        await asyncio.sleep(2)
        elapsed = time.time() - _last_ping
        if elapsed > WATCHDOG_TIMEOUT_S:
            print(f"[WDT] Timeout หลัง {elapsed}s — กำลัง reset!")
            await asyncio.sleep_ms(100)
            machine.reset()

async def main_task():
    while True:
        ping_watchdog()       # ต้อง ping ทุกๆ < 10 วินาที
        print("Working...")
        await asyncio.sleep(3)

async def main():
    asyncio.create_task(software_watchdog())
    asyncio.create_task(main_task())
    await asyncio.sleep(60)

asyncio.run(main())
```

---

## 15. Pattern: Debounce ปุ่มด้วย async

ป้องกัน bouncing โดยไม่ใช้ `time.sleep()` ที่บล็อก event loop

```python
import asyncio
from machine import Pin

DEBOUNCE_MS = 50

async def debounced_button(pin_num: int, callback):
    """
    รอกด → รอ debounce → ตรวจยืนยัน → เรียก callback
    """
    pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
    last_state = pin.value()

    while True:
        await asyncio.sleep_ms(10)  # polling interval
        current = pin.value()

        if current != last_state:
            await asyncio.sleep_ms(DEBOUNCE_MS)  # รอ bounce หายไป
            confirmed = pin.value()
            if confirmed == current:
                last_state = current
                if current == 0:  # falling edge = กด
                    await callback()

# ─── ตัวอย่างการใช้ ───────────────────────────────────────
press_count = 0

async def on_press():
    global press_count
    press_count += 1
    print(f"[BTN] กดครั้งที่ {press_count}")

async def main():
    asyncio.create_task(debounced_button(0, on_press))
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```

---

## 16. ข้อควรระวังและ Anti-pattern

### ❌ อย่าใช้ `time.sleep()` ใน async

```python
# ❌ บล็อก event loop ทั้งหมด
async def bad_task():
    import time
    time.sleep(1)   # task อื่นหยุดทำงานทั้งหมด!

# ✅ ถูกต้อง
async def good_task():
    await asyncio.sleep(1)  # ยอมสละ CPU
```

### ❌ อย่าทำงานหนักใน loop โดยไม่ await

```python
# ❌ คำนวณนาน 500ms โดยไม่มี await
async def bad_compute():
    result = 0
    for i in range(1_000_000):
        result += i  # บล็อก 500ms!

# ✅ แบ่งงานและ yield CPU เป็นระยะ
async def good_compute():
    result = 0
    for i in range(1_000_000):
        result += i
        if i % 10_000 == 0:
            await asyncio.sleep(0)  # yield ทุก 10,000 รอบ
```

### ❌ อย่าเรียก coroutine โดยไม่ await

```python
async def my_func():
    pass

# ❌ ไม่ทำงาน — สร้าง coroutine object แต่ไม่รัน
my_func()

# ✅ ต้อง await หรือ create_task
await my_func()
asyncio.create_task(my_func())
```

### ❌ อย่าใช้ global mutable state โดยไม่มี Lock

```python
# ❌ อาจเกิด race condition ถ้า 2 task เขียนพร้อมกัน
shared_data = {}

# ✅ ใช้ Lock ป้องกัน
data_lock = asyncio.Lock()
async def safe_write(key, val):
    async with data_lock:
        shared_data[key] = val
```

### ❌ อย่า forget re-raise CancelledError

```python
# ❌ กลืน CancelledError ทำให้ cancel ไม่ทำงาน
async def bad():
    try:
        await asyncio.sleep(10)
    except Exception:
        pass  # กลืน CancelledError!

# ✅
async def good():
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        # cleanup
        raise  # ต้อง re-raise
    except Exception as e:
        print(e)
```

---

## 17. เปรียบเทียบ asyncio.sleep vs time.sleep

| | `await asyncio.sleep()` | `time.sleep()` |
|---|---|---|
| บล็อก event loop | ❌ ไม่บล็อก | ✅ บล็อกทุก task |
| ใช้ใน async function | ✅ ต้องใช้ | ⚠️ ได้แต่ผิด pattern |
| ใช้ใน ISR / thread | ❌ ไม่ได้ | ✅ ได้ |
| ความแม่นยำ | ±1ms (ขึ้นกับ loop) | สูงกว่า |
| เหมาะสำหรับ | งาน async ทั่วไป | boot, init ที่ยังไม่มี loop |

---

## 18. Memory และ Performance Tips

### 1. ใช้ `asyncio.sleep_ms()` แทน `asyncio.sleep()`

```python
await asyncio.sleep_ms(100)   # เร็วกว่า ไม่ต้องแปลง float
```

### 2. เรียก `gc.collect()` ใน idle task

```python
async def gc_task():
    while True:
        gc.collect()
        await asyncio.sleep(30)
```

### 3. จำกัดขนาด Queue

```python
q = asyncio.Queue(maxsize=10)  # กำหนด maxsize เสมอ ป้องกัน RAM ล้น
```

### 4. หลีกเลี่ยง lambda ใน create_task

```python
# ❌ สร้าง closure object ใช้ RAM
asyncio.create_task(lambda: my_func(arg))

# ✅ สร้าง coroutine โดยตรง
asyncio.create_task(my_func(arg))
```

### 5. ใช้ `__slots__` ใน class ที่สร้างบ่อย

```python
class SensorData:
    __slots__ = ('id', 'value', 'ts')
    def __init__(self, id, value, ts):
        self.id = id
        self.value = value
        self.ts = ts
```

### 6. ตรวจสอบ RAM ว่าง

```python
async def health_monitor():
    import gc
    while True:
        gc.collect()
        free = gc.mem_free()
        if free < 5000:
            print(f"[WARN] RAM เหลือน้อย: {free} bytes")
        await asyncio.sleep(10)
```

---

## สรุปภาพรวม

```
Primitive         ใช้เมื่อ
─────────────────────────────────────────────────────────────
asyncio.sleep     หน่วงเวลาโดยไม่บล็อก
create_task       รัน coroutine พร้อมกัน
gather            รอทุก coroutine เสร็จพร้อมกัน
Event             ส่งสัญญาณ "เกิดเหตุการณ์" ระหว่าง task
Lock              ป้องกัน shared resource (I2C, SPI, file)
Queue             ส่งข้อมูลระหว่าง task แบบ FIFO
wait_for          กำหนด timeout ให้ coroutine
StreamReader/     I/O แบบ async (UART, TCP)
  StreamWriter
ThreadSafeFlag    สื่อสารจาก ISR/thread → async task
```
