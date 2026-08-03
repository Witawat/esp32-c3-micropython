"""
Import Smoke Test สำหรับ lib/ ทั้งหมด (host-side)
รันด้วย:  .venv\\Scripts\\python.exe src\\tests\\check_import.py

วิธีการ:
- เพิ่ม src/tests/mocks เข้า sys.path (mock MicroPython modules)
- import ทุก .py module ใน lib/ ทีละตัว
- รายงาน ImportError / NameError / SyntaxError / โค้ดระดับ module
"""

import importlib
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # src/
LIB_DIR = os.path.join(ROOT, "lib")
MOCK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mocks")

sys.path.insert(0, MOCK_DIR)
sys.path.insert(0, LIB_DIR)

# ── เก็บไฟล์ import ทั้งหมด ─────────────────────────────────
MODULES = []
for entry in sorted(os.listdir(LIB_DIR)):
    full = os.path.join(LIB_DIR, entry)
    if os.path.isdir(full):
        if not os.path.isfile(os.path.join(full, "__init__.py")):
            continue
        MODULES.append(entry)  # package itself
        for f in sorted(os.listdir(full)):
            if f.endswith(".py") and f != "__init__.py":
                mod = f"{entry}.{f[:-3]}"
                MODULES.append(mod)
    elif entry.endswith(".py"):
        MODULES.append(entry[:-3])

MODULES = sorted(set(MODULES))


def safe_import(name):
    try:
        importlib.import_module(name)
        return None
    except SystemExit:
        return "SystemExit"
    except Exception as e:
        tb = traceback.format_exc().strip().splitlines()
        return f"{type(e).__name__}: {e}\n  {tb[-1] if tb else ''}"


def main():
    passed, failed = [], []
    for name in MODULES:
        err = safe_import(name)
        if err is None:
            passed.append(name)
        else:
            failed.append((name, err))

    print(f"=== Import Smoke Test: {len(MODULES)} modules ===")
    print(f"[PASS]: {len(passed)}")
    print(f"[FAIL]: {len(failed)}\n")

    if failed:
        print("----- FAILED -----")
        for name, err in failed:
            print(f"\n[{name}]")
            print(f"  {err}")

    # exit code
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
