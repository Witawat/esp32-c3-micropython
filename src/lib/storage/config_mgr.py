"""
JSON Config Manager
รองรับ: MicroPython / CPython
"""

import json
import os


class JsonConfigManager:
    """
    จัดการไฟล์ config แบบ JSON ให้ใช้งานร่วมกันทุกโมดูล
    """

    def __init__(self, path: str, auto_create: bool = True):
        self.path = path
        self.auto_create = auto_create

    def exists(self) -> bool:
        try:
            os.stat(self.path)
            return True
        except OSError:
            return False

    def load(self, default: dict = None) -> dict:
        if default is None:
            default = {}

        if not self.exists():
            if self.auto_create:
                self.save(default)
            return default.copy()

        try:
            with open(self.path, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            print("⚠️ load config error:", e)
        return default.copy()

    def save(self, data: dict) -> bool:
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w") as f:
                json.dump(data, f)
            try:
                os.remove(self.path)
            except OSError:
                pass
            os.rename(tmp, self.path)
            return True
        except Exception as e:
            print("❌ save config error:", e)
            try:
                os.remove(tmp)
            except OSError:
                pass
            return False

    def update(self, patch: dict, default: dict = None) -> dict:
        data = self.load(default=default)
        data.update(patch)
        self.save(data)
        return data

    def get(self, key, default=None):
        return self.load().get(key, default)

    def set(self, key, value) -> bool:
        data = self.load()
        data[key] = value
        return self.save(data)

    def delete_key(self, key) -> bool:
        data = self.load()
        if key in data:
            del data[key]
        return self.save(data)

    def reset(self, data: dict = None) -> bool:
        return self.save(data or {})
