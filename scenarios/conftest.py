"""Root conftest for scenarios - mocks micropython before test discovery."""
import sys
import os
import random
from types import ModuleType

# Mock micropython module BEFORE pytest discovers MockUI package
# Pattern from specter-diy: libs/common/embit/misc.py
if "micropython" not in sys.modules:
    micropython_mock = ModuleType("micropython")
    micropython_mock.const = lambda x: x
    sys.modules["micropython"] = micropython_mock

# Mock urandom (MicroPython's random bytes module)
if "urandom" not in sys.modules:
    urandom_mock = ModuleType("urandom")
    urandom_mock.getrandbits = lambda n: random.getrandbits(n)
    urandom_mock.randint = random.randint
    urandom_mock.choice = random.choice
    sys.modules["urandom"] = urandom_mock

# Mock utime (MicroPython's time module)
if "utime" not in sys.modules:
    import time
    utime_mock = ModuleType("utime")
    utime_mock.sleep_ms = lambda ms: time.sleep(ms / 1000)
    utime_mock.ticks_ms = lambda: int(time.time() * 1000)
    sys.modules["utime"] = utime_mock

# Mock lvgl module to prevent LVGL imports from failing
if "lvgl" not in sys.modules:
    class LvMockObj:
        """Mock LVGL base object."""
        def __init__(self, *args, **kwargs):
            pass

    class LvMockEvent:
        CLICKED = 1

    lvgl_mock = ModuleType("lvgl")
    lvgl_mock.color_hex = lambda x: x
    lvgl_mock.obj = LvMockObj
    lvgl_mock.label = LvMockObj
    lvgl_mock.button = LvMockObj
    lvgl_mock.bar = LvMockObj
    lvgl_mock.textarea = LvMockObj
    lvgl_mock.keyboard = LvMockObj
    lvgl_mock.switch = LvMockObj
    lvgl_mock.image = LvMockObj
    lvgl_mock.EVENT = LvMockEvent
    lvgl_mock.ALIGN = type("ALIGN", (), {"CENTER": 0, "TOP_LEFT": 1, "TOP_RIGHT": 2, "BOTTOM_LEFT": 3, "BOTTOM_RIGHT": 4})()
    lvgl_mock.SYMBOL = type("SYMBOL", (), {"BATTERY_FULL": "F", "BATTERY_3": "3", "BATTERY_2": "2", "BATTERY_1": "1", "BATTERY_EMPTY": "E", "CHARGE": "C"})()
    lvgl_mock.FLEX_FLOW = type("FLEX_FLOW", (), {"COLUMN": 0, "ROW": 1})()
    lvgl_mock.FLEX_ALIGN = type("FLEX_ALIGN", (), {"START": 0, "CENTER": 1, "END": 2, "SPACE_BETWEEN": 3})()
    sys.modules["lvgl"] = lvgl_mock
