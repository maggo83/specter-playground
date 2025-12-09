from ..basic import RED, ORANGE, RED_HEX, GenericMenu
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv

def DeviceMenu(parent, *args, **kwargs):
    on_navigate = getattr(parent, "on_navigate", None)
    state = getattr(parent, "specter_state", None)

    menu_items = [(None, "Manage Device", None, None)]

    if state and state.hasSD and state.enabledSD and state.detectedSD:
        menu_items.append((BTC_ICONS.COPY, "Manage Backup(s)", "manage_backups", None))

    if state and ((state.hasQR and state.enabledQR) or (state.hasSD and state.enabledSD and state.detectedSD) or (state.hasUSB and state.enabledUSB)):
        menu_items.append((BTC_ICONS.CODE, "Manage Firmware", "manage_firmware", None))

    menu_items += [
        (BTC_ICONS.SHIELD, "Manage Security Features", "manage_security", None),
        (BTC_ICONS.FLIP_HORIZONTAL, "Enable/Disable Interfaces", "interfaces", None),
        (BTC_ICONS.PHOTO, "Manage Display", "display_settings", None),
        (lv.SYMBOL.VOLUME_MAX, "Manage Sounds", "sound_settings", None)
    ]

    menu_items += [
        (None, ORANGE + " " + lv.SYMBOL.WARNING+ " Dangerzone#", None, None),
        (BTC_ICONS.ALERT_CIRCLE, "Wipe Device", "wipe_device", RED_HEX)
    ]


    return GenericMenu("manage_device", "Manage Device/Storage", menu_items, parent, *args, **kwargs)
