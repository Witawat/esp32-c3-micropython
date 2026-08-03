"""Alias mock: uos -> os (MicroPython u-prefixed stdlib)"""

import os as _o
import sys

getcwd = _o.getcwd
listdir = _o.listdir
mkdir = _o.mkdir
remove = _o.remove
rename = _o.rename
stat = _o.stat
unlink = _o.unlink


def chdir(path):
    return _o.chdir(path)


def rmdir(path):
    return _o.rmdir(path)


def sep():
    return _o.sep


def uname():
    return ("mock", "machine", "1.0", "v1.28", "host")
