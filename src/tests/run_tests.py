"""
Test runner: discover + run ทุก test_*.py ใน src/tests
วิธีรัน:  python run_tests.py   (จาก src/tests)
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

loader = unittest.TestLoader()
suite = loader.discover(start_dir=HERE, pattern="test_*.py", top_level_dir=HERE)
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
