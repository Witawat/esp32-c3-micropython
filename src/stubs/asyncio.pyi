# asyncio stub สำหรับ MicroPython
# เพิ่ม sleep_ms และ sleep_us ที่ไม่มีใน CPython asyncio typeshed

from asyncio import *
from asyncio import (
    AbstractEventLoop,
    CancelledError,
    Task,
    TimeoutError,
    create_task,
    current_task,
    get_event_loop,
    run,
    sleep,
    wait_for,
)
from typing import Awaitable


# MicroPython-specific additions
def sleep_ms(ms: int) -> Awaitable[None]:
    """หยุดรอ N มิลลิวินาที (MicroPython uasyncio)"""
    ...

def sleep_us(us: int) -> Awaitable[None]:
    """หยุดรอ N ไมโครวินาที (MicroPython uasyncio)"""
    ...
