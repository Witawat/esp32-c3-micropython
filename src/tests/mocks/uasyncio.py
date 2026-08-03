"""Alias mock: uasyncio -> asyncio (MicroPython u-prefixed stdlib)"""

import asyncio as _a

sleep = _a.sleep
create_task = _a.create_task
gather = _a.gather
run = _a.run
Task = _a.Task
Lock = _a.Lock
Event = _a.Event
Queue = getattr(_a, "Queue", None)
CancelledError = getattr(_a, "CancelledError", Exception)
