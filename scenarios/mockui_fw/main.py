# main.py - MockUI entry point (STM32F469 Discovery + unix simulator)
import gc
import sys
import display
import lvgl as lv
import utime as time

# Detect platform: sys.platform is 'linux'/'darwin' on unix simulator,
# 'pyboard' on STM32 hardware. (import pyb is NOT reliable — a stub exists for unix.)
_ON_HARDWARE = sys.platform not in ('linux', 'darwin')

# --- Simulator environment setup (the only place with platform-specific logic) ---
if not _ON_HARDWARE:
    import os
    # Mount build/flash_image as /flash so firmware code sees the same path as on
    # hardware. make build-i18n places lang_*.bin files in build/flash_image/i18n/.
    # os.getcwd() is the project root when launched via `make simulate`.
    os.mount(os.VfsPosix(os.getcwd() + '/build/flash_image'), '/flash')
    # Disable SDL autoupdate so our manual loop drives it.
    display.init(False)
else:
    # Hardware: display.init() disables the autoupdate timer internally.
    display.init()
# --- End simulator setup ---

from MockUI import SpecterGui, SpecterState

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

scr = SpecterGui(specter_state)
lv.screen_load(scr)

# Start TCP control server when --control flag is passed (simulator only)
if not _ON_HARDWARE and '--control' in sys.argv:
    from sim_control import ControlServer
    ControlServer(scr)

while True:
    display.update(30)
    time.sleep_ms(30)
