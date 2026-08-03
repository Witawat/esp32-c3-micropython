"""
Environment setup สำหรับ test files
- เพิ่ม mocks + lib เข้า sys.path
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # src/

sys.path.insert(0, os.path.join(HERE, "mocks"))
sys.path.insert(0, os.path.join(ROOT, "lib"))
