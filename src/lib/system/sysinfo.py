"""
System Information Utility
"""

import machine
import os
import gc


class SysInfo:
    @staticmethod
    def cpu_freq_hz():
        return machine.freq()

    @staticmethod
    def chip_id_hex():
        uid = machine.unique_id()
        return "".join(["%02x" % b for b in uid])

    @staticmethod
    def reset_cause():
        return machine.reset_cause()

    @staticmethod
    def wake_reason():
        if hasattr(machine, "wake_reason"):
            return machine.wake_reason()
        return None

    @staticmethod
    def mem_free():
        gc.collect()
        return gc.mem_free()

    @staticmethod
    def mem_alloc():
        gc.collect()
        return gc.mem_alloc()

    @staticmethod
    def fs_usage(path="/"):
        st = os.statvfs(path)
        total = st[0] * st[2]
        free = st[0] * st[3]
        used = total - free
        return {
            "path": path,
            "total": total,
            "used": used,
            "free": free,
        }

    @classmethod
    def all(cls):
        return {
            "cpu_freq_hz": cls.cpu_freq_hz(),
            "chip_id": cls.chip_id_hex(),
            "reset_cause": cls.reset_cause(),
            "wake_reason": cls.wake_reason(),
            "mem_free": cls.mem_free(),
            "mem_alloc": cls.mem_alloc(),
            "fs": cls.fs_usage("/"),
        }
