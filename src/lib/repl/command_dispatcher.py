"""
Command Dispatcher Module สำหรับ ESP32-C3
จัดการการลงทะเบียนและ dispatch คำสั่ง REPL

วิธีใช้งาน:
    from repl.command_dispatcher import CommandDispatcher

    dispatcher = CommandDispatcher(prompt="esp32> ")

    @dispatcher.command("led", "เปิด/ปิด LED")
    def led_cmd(*args):
        state = args[0] if args else "on"
        return f"✅ LED {state.upper()}"

    response = dispatcher.dispatch("led on")
    print(response)  # ✅ LED ON
"""

import gc


class CommandDispatcher:
    """
    จัดการการลงทะเบียน command และ dispatch คำสั่งไปยัง handler
    ใช้ร่วมกับ transport layer (TCP, UART, BLE, WebREPL)
    """

    def __init__(self, prompt="esp32> ", exec_enabled=False, welcome=None):
        """
        สร้าง instance ของ CommandDispatcher

        Args:
            prompt (str): prompt string ที่แสดงหลังส่ง response (default: "esp32> ")
            exec_enabled (bool): เปิดใช้ raw exec() mode (default: False) ⚠️ ความเสี่ยงด้านความปลอดภัย
            welcome (str): ข้อความต้อนรับเมื่อ client เชื่อมต่อ (default: None)
        """
        self.prompt = prompt
        self.exec_enabled = exec_enabled
        self.welcome = welcome or f"ESP32 REPL — พิมพ์ 'help' เพื่อดูคำสั่งทั้งหมด\r\n{prompt}"
        self._commands = {}
        self._exec_globals = {}

        # ลงทะเบียน built-in commands
        self._register_builtins()

    # ──────────────────────────────────────────
    # Registration
    # ──────────────────────────────────────────

    def register(self, name, handler, description=""):
        """
        ลงทะเบียน command

        Args:
            name (str): ชื่อ command (case-insensitive)
            handler (callable): ฟังก์ชัน handler — signature: handler(*args) -> str
            description (str): คำอธิบาย command (แสดงใน help)
        """
        self._commands[name.lower()] = {
            "handler": handler,
            "description": description,
        }

    def unregister(self, name):
        """
        ลบ command ออกจาก dispatcher

        Args:
            name (str): ชื่อ command ที่ต้องการลบ

        Returns:
            bool: True ถ้าลบสำเร็จ
        """
        key = name.lower()
        if key in self._commands:
            del self._commands[key]
            return True
        return False

    def command(self, name, description=""):
        """
        Decorator สำหรับลงทะเบียน command แบบ shorthand

        Args:
            name (str): ชื่อ command
            description (str): คำอธิบาย command

        Example:
            @dispatcher.command("ping", "ทดสอบการตอบสนอง")
            def ping_cmd(*args):
                return "pong"
        """
        def decorator(func):
            self.register(name, func, description)
            return func
        return decorator

    def list_commands(self):
        """
        คืน dict ของ commands ทั้งหมดที่ลงทะเบียนไว้

        Returns:
            dict: {name: description}
        """
        return {k: v["description"] for k, v in self._commands.items()}

    # ──────────────────────────────────────────
    # Dispatching
    # ──────────────────────────────────────────

    def dispatch(self, line):
        """
        Parse input line และ dispatch ไปยัง handler

        Args:
            line (str): input จาก user เช่น "led on" หรือ "temp read"

        Returns:
            str: response ที่จะส่งกลับไปยัง client (รวม newline + prompt)
        """
        if not line:
            return self.prompt

        line = line.strip()
        if not line:
            return self.prompt

        # แยก command และ arguments
        parts = line.split()
        cmd_name = parts[0].lower()
        args = parts[1:]

        # ตรวจสอบ exec command
        if cmd_name == "exec":
            return self._handle_exec(args)

        # หา handler
        entry = self._commands.get(cmd_name)
        if entry is None:
            return f"❌ ไม่รู้จักคำสั่ง '{cmd_name}' — พิมพ์ 'help' เพื่อดูคำสั่งทั้งหมด\r\n{self.prompt}"

        # รัน handler
        try:
            result = entry["handler"](*args)
            if result is None:
                result = "OK"
            return f"{result}\r\n{self.prompt}"
        except TypeError as e:
            return f"❌ argument ไม่ถูกต้อง: {e}\r\n{self.prompt}"
        except Exception as e:
            return f"❌ เกิดข้อผิดพลาด: {e}\r\n{self.prompt}"

    # ──────────────────────────────────────────
    # Built-in commands
    # ──────────────────────────────────────────

    def _register_builtins(self):
        """ลงทะเบียน built-in commands"""
        self.register("help", self._cmd_help, "แสดงรายการคำสั่งทั้งหมด")
        self.register("mem", self._cmd_mem, "แสดง free memory (bytes)")
        self.register("gc", self._cmd_gc, "รัน garbage collector")
        self.register("echo", self._cmd_echo, "แสดงข้อความที่ส่งมา (ทดสอบ)")

    def _cmd_help(self, *args):
        """แสดง help"""
        lines = ["📋 คำสั่งที่รองรับ:", ""]
        for name, entry in sorted(self._commands.items()):
            desc = entry["description"] or "(ไม่มีคำอธิบาย)"
            lines.append(f"  {name:<16} {desc}")
        if self.exec_enabled:
            lines.append("")
            lines.append("  exec <code>      รัน Python code โดยตรง (exec mode เปิดอยู่)")
        lines.append("")
        lines.append(f"รวม {len(self._commands)} คำสั่ง")
        return "\r\n".join(lines)

    def _cmd_mem(self, *args):
        """แสดง free memory"""
        free = gc.mem_free()
        alloc = gc.mem_alloc()
        total = free + alloc
        return f"🧠 Memory: free={free}B  alloc={alloc}B  total={total}B"

    def _cmd_gc(self, *args):
        """รัน garbage collector"""
        before = gc.mem_free()
        gc.collect()
        after = gc.mem_free()
        freed = after - before
        return f"🗑 GC เสร็จสิ้น: เพิ่ม {freed}B (ตอนนี้ free={after}B)"

    def _cmd_echo(self, *args):
        """echo ข้อความ"""
        return " ".join(args) if args else "(ว่าง)"

    def _handle_exec(self, args):
        """รัน raw Python code ผ่าน exec()"""
        if not self.exec_enabled:
            return f"❌ exec mode ปิดอยู่ — ตั้ง exec_enabled=True เพื่อเปิด\r\n{self.prompt}"

        code = " ".join(args)
        if not code:
            return f"❌ ใช้: exec <python code>\r\n{self.prompt}"

        try:
            # รัน exec ใน isolated globals dict
            exec(code, self._exec_globals)  # noqa: S102
            gc.collect()
            return f"OK\r\n{self.prompt}"
        except Exception as e:
            return f"❌ exec error: {e}\r\n{self.prompt}"
