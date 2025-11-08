from ..basic import RED, ORANGE, RED_HEX, GenericMenu
import lvgl as lv

def DeviceMenu(parent, *args, **kwargs):
    on_navigate = getattr(parent, "on_navigate", None)
    state = getattr(parent, "specter_state", None)

    menu_items = [(None, "Manage Device", None, None)]

    if state and state.hasSD and state.enabledSD and state.detectedSD:
        menu_items.append((lv.SYMBOL.COPY, "Manage Backup(s)", "manage_backups", None))

    if state and ((state.hasQR and state.enabledQR) or (state.hasSD and state.enabledSD and state.detectedSD) or (state.hasUSB and state.enabledUSB)):
        menu_items.append((None, "Manage Firmware", "manage_firmware", None))

    menu_items += [
        (lv.SYMBOL.BELL, "Manage Security Features", "manage_security", None),
        (None, "Enable/Disable Interfaces", "interfaces", None),
        (lv.SYMBOL.IMAGE, "Manage Display", "display_settings", None),
        (lv.SYMBOL.VOLUME_MAX, "Manage Sounds", "sound_settings", None)
    ]

    menu_items += [
        (None, ORANGE + " Dangerzone#", None, None),
        (lv.SYMBOL.WARNING, "Wipe Device", "wipe_device", RED_HEX)
    ]


    return GenericMenu("manage_device", "Manage Device/Storage", menu_items, parent, *args, **kwargs)
