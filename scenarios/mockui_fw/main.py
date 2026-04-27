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

specter_state._hasQR = True
specter_state._enabledQR = True

specter_state._hasSD = True
specter_state._enabledSD = False
specter_state._detectedSD = True
specter_state._SD_hasSeed = True

specter_state._hasSmartCard = True
specter_state._enabledSmartCard = True
specter_state._detectedSmartCard = True
specter_state._SmartCard_hasSeed = True

specter_state._Flash_hasSeed = True

specter_state.pin = "21"

gc.collect()

scr = SpecterGui(specter_state)
lv.screen_load(scr)

# Start TCP control server when --control flag is passed (simulator only)
if not _ON_HARDWARE and '--control' in sys.argv:
    from sim_control import ControlServer
    ControlServer(scr)

_last_tick = time.ticks_ms()
while True:
    now = time.ticks_ms()
    elapsed = time.ticks_diff(now, _last_tick)
    _last_tick = now
    # Cap the tick increment so LVGL never skips animation frames.
    # If a render+flush takes 50ms, telling LVGL "50ms elapsed" makes a
    # 150ms animation finish in 3 frames. Capping at 16ms gives >=9 frames
    # regardless of actual frame rate.
    display.update(min(elapsed, 16) if _ON_HARDWARE else elapsed)
    time.sleep_ms(0 if _ON_HARDWARE else 20)
