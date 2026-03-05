# main.py - MockUI entry point (STM32F469 Discovery + unix simulator)
import gc
import sys
import display
import lvgl as lv
import utime as time

# Detect platform: pyb is hardware-only, not present on unix simulator
try:
    import pyb as _pyb
    _ON_HARDWARE = True
except ImportError:
    _pyb = None
    _ON_HARDWARE = False

from MockUI import NavigationController, SpecterState

# Init display.
# Hardware: display.init() disables the autoupdate timer (avoids heap fragmentation).
# Simulator: display.init(False) disables SDL autoupdate so we drive the loop manually.
if _ON_HARDWARE:
    display.init()
else:
    display.init(False)

gc.collect()

lv.theme_default_init(
    None,
    lv.palette_main(lv.PALETTE.BLUE_GREY),
    lv.palette_main(lv.PALETTE.RED),
    True,
    lv.font_montserrat_16,
)

specter_state = SpecterState()
specter_state.has_battery = True
specter_state.battery_pct = 100

specter_state.hasQR = True
specter_state.enabledQR = True

specter_state.hasSD = True
specter_state.enabledSD = False
specter_state.detectedSD = True

specter_state.hasSmartCard = True
specter_state.enabledSmartCard = True
specter_state.detectedSmartCard = True

specter_state.seed_loaded = False
specter_state.active_passphrase = ""
specter_state.pin = "21"

gc.collect()

scr = NavigationController(specter_state)
lv.screen_load(scr)

# Start TCP control server when --control flag is passed (simulator only)
if not _ON_HARDWARE and '--control' in sys.argv:
    from sim_control import ControlServer
    ControlServer(scr)

# Enable USB REPL for debugging (hardware only)
if _ON_HARDWARE:
    _pyb.usb_mode("VCP")

while True:
    display.update(30)
    time.sleep_ms(30)
