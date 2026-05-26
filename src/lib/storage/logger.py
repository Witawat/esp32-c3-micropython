"""
File Logger
รองรับ: Internal Flash / SD Card
"""

import time
import os


class FileLogger:
    LEVEL_DEBUG = 10
    LEVEL_INFO = 20
    LEVEL_WARN = 30
    LEVEL_ERROR = 40

    LEVEL_NAMES = {
        LEVEL_DEBUG: "DEBUG",
        LEVEL_INFO: "INFO",
        LEVEL_WARN: "WARN",
        LEVEL_ERROR: "ERROR",
    }

    def __init__(self, file_path: str = "app.log", level: int = LEVEL_INFO,
                 max_bytes: int = 128 * 1024, backup_count: int = 2):
        self.file_path = file_path
        self.level = level
        self.max_bytes = max_bytes
        self.backup_count = backup_count

    def set_level(self, level: int):
        self.level = level

    def _timestamp(self) -> str:
        t = time.localtime()
        return "%04d-%02d-%02d %02d:%02d:%02d" % (t[0], t[1], t[2], t[3], t[4], t[5])

    def _should_rotate(self) -> bool:
        try:
            return os.stat(self.file_path)[6] >= self.max_bytes
        except OSError:
            return False

    def _rotate(self):
        if self.backup_count <= 0:
            return

        oldest = "%s.%d" % (self.file_path, self.backup_count)
        try:
            os.remove(oldest)
        except OSError:
            pass

        i = self.backup_count - 1
        while i >= 1:
            src = "%s.%d" % (self.file_path, i)
            dst = "%s.%d" % (self.file_path, i + 1)
            try:
                os.rename(src, dst)
            except OSError:
                pass
            i -= 1

        try:
            os.rename(self.file_path, self.file_path + ".1")
        except OSError:
            pass

    def log(self, level: int, message: str):
        if level < self.level:
            return

        if self._should_rotate():
            self._rotate()

        line = "%s [%s] %s\n" % (self._timestamp(), self.LEVEL_NAMES.get(level, str(level)), message)
        with open(self.file_path, "a") as f:
            f.write(line)

    def debug(self, message: str):
        self.log(self.LEVEL_DEBUG, message)

    def info(self, message: str):
        self.log(self.LEVEL_INFO, message)

    def warn(self, message: str):
        self.log(self.LEVEL_WARN, message)

    def error(self, message: str):
        self.log(self.LEVEL_ERROR, message)
