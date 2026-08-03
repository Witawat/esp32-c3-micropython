"""Mock module: micropython (MicroPython built-in)"""

import builtins


def const(expr):
    return expr


def schedule(func, arg):
    return None


def alloc_emergency_exception_buf(size):
    return None


def heap_lock():
    return None


def heap_unlock():
    return None


def kbd_intr(chr):
    return None


def mem_info(*args):
    return None


def opt_level(level=None):
    return 0


def qstr_info(*args):
    return None


def stack_use():
    return 0


def version():
    return "1.28.0"


def version_tuple():
    return (1, 28, 0)


class OSError:
    def __init__(self, *args):
        pass
