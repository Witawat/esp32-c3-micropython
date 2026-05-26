"""
Audit Logger — บันทึกทุกคำสั่ง REPL เพื่อตรวจสอบภายหลัง
Interface: File I/O (FIFO buffer)
รองรับ: ESP32 ทุกรุ่น

Features:
- บันทึกทุกคำสั่ง REPL: timestamp, transport, command, result
- FIFO buffer (max 10KB) — ป้องกัน flash wear
- Suspicious pattern detection
- Log rotation (เก็บใน RAM + flush to flash)
"""

import time
import gc


class AuditLogger:
    """
    Audit Logger — บันทึกคำสั่ง REPL เพื่อ forensic analysis

    ใช้ตรวจจับการบุกรุกและตรวจสอบว่าใครทำอะไรผ่าน REPL

    ตัวอย่าง:
        audit = AuditLogger(log_file='audit.log')
        audit.log_command('tcp', 'led on', '✅ LED ON')
        audit.log_event('SECURITY', 'Failed auth attempt #3')
        print(audit.get_recent_logs(5))

    Log format:
        [TIMESTAMP] LEVEL TRANSPORT | COMMAND → RESULT
    """

    LEVEL_INFO = 'INFO'
    LEVEL_WARN = 'WARN'
    LEVEL_ERROR = 'ERROR'
    LEVEL_SECURITY = 'SECURITY'

    def __init__(self, log_file: str = 'audit.log',
                 max_entries: int = 100,
                 max_file_bytes: int = 10240):
        """
        :param log_file: ชื่อไฟล์ log
        :param max_entries: จำนวน entry สูงสุดใน RAM buffer
        :param max_file_bytes: ขนาดไฟล์สูงสุด (bytes) — FIFO
        """
        self._log_file = log_file
        self._max_entries = max_entries
        self._max_file_bytes = max_file_bytes
        self._buffer = []  # RAM buffer: [(timestamp, level, transport, command, result)]
        self._write_count = 0
        self._suspicious_count = 0

        print(f"📝 AuditLogger เริ่มต้น — {log_file} (max={max_file_bytes}B)")

    # ── Logging ───────────────────────────────────────────

    def log_command(self, transport: str, command: str, result: str):
        """
        บันทึกคำสั่ง REPL

        :param transport: 'uart', 'tcp', 'ble', 'web'
        :param command: คำสั่งที่ผู้ใช้พิมพ์
        :param result: ผลลัพธ์ (ตัดเหลือ 80 chars)
        """
        self._log(self.LEVEL_INFO, transport, command, result[:80])

    def log_event(self, level: str, message: str):
        """
        บันทึก event (ไม่เกี่ยวกับคำสั่งโดยตรง)

        :param level: INFO, WARN, ERROR, SECURITY
        :param message: ข้อความ
        """
        self._log(level, 'SYSTEM', '', message)

    def _log(self, level: str, transport: str, command: str, result: str):
        """Internal log method"""
        now = time.ticks_ms()
        entry = (now, level, transport, command, result)

        # Add to RAM buffer (FIFO)
        self._buffer.append(entry)
        if len(self._buffer) > self._max_entries:
            self._buffer.pop(0)  # FIFO

        # Flush to flash (every 10 writes or on error/security)
        self._write_count += 1
        if (self._write_count % 10 == 0 or
                level in (self.LEVEL_ERROR, self.LEVEL_SECURITY)):
            self._flush()

        # Detect suspicious patterns
        self._detect_suspicious(level, transport, command)

        # Free memory
        gc.collect()

    # ── Flush to Flash ────────────────────────────────────

    def _flush(self):
        """เขียน buffer ลง flash — ป้องกันการเขียนถี่เกิน"""
        try:
            # Read existing log
            existing = b''
            try:
                with open(self._log_file, 'rb') as f:
                    existing = f.read()
            except OSError:
                pass

            # Append new entries
            new_lines = []
            for entry in self._buffer[-10:]:  # last 10 entries
                ts, level, transport, cmd, result = entry
                line = (f"[{ts}] {level:8s} {transport:6s} | "
                        f"{cmd[:40]:40s} → {result[:40]}\n")
                new_lines.append(line)

            new_data = ''.join(new_lines).encode('utf-8')
            combined = existing + new_data

            # FIFO: keep only last max_file_bytes
            if len(combined) > self._max_file_bytes:
                combined = combined[-self._max_file_bytes:]

            with open(self._log_file, 'wb') as f:
                f.write(combined)

        except OSError as e:
            print(f"⚠️ AuditLogger flush failed: {e}")

    # ── Suspicious Detection ──────────────────────────────

    def _detect_suspicious(self, level: str, transport: str, command: str):
        """ตรวจจับ suspicious patterns"""
        suspicious_keywords = [
            'exec', 'import os', 'import machine',
            'open(', 'remove(', 'rename(',
            '__import__', 'compile(', 'eval(',
            'webrepl.start', 'sys.path',
        ]

        cmd_lower = command.lower()
        for kw in suspicious_keywords:
            if kw in cmd_lower:
                self._suspicious_count += 1
                print(f"🚨 AUDIT: Suspicious command detected — '{command}' "
                      f"via {transport}")

    # ── Query ─────────────────────────────────────────────

    def get_recent_logs(self, count: int = 20) -> list:
        """
        อ่าน log ล่าสุดจาก RAM buffer

        :param count: จำนวน entries
        :return: list of (timestamp, level, transport, command, result)
        """
        return list(self._buffer[-count:])

    def get_all_logs(self) -> list:
        """อ่าน log ทั้งหมดจาก RAM"""
        return list(self._buffer)

    def get_suspicious_count(self) -> int:
        """จำนวน suspicious events ที่ตรวจพบ"""
        return self._suspicious_count

    def read_log_file(self) -> str:
        """
        อ่านไฟล์ log จาก flash

        :return: เนื้อหาไฟล์ (string)
        """
        try:
            with open(self._log_file, 'r') as f:
                return f.read()
        except OSError:
            return ''

    # ── Cleanup ───────────────────────────────────────────

    def clear_logs(self):
        """ล้าง log ทั้งหมด (RAM + flash)"""
        self._buffer.clear()
        self._suspicious_count = 0
        try:
            open(self._log_file, 'w').close()
        except OSError:
            pass
        print("📝 AuditLogger: logs cleared")

    def flush(self):
        """Force flush to flash"""
        self._flush()
        print("📝 AuditLogger: flushed to flash")
