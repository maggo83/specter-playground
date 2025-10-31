from ..basic import RED, ORANGE, GenericMenu
import lvgl as lv

def DeviceMenu(parent, *args, **kwargs):
    on_navigate = getattr(parent, "on_navigate", None)
    state = getattr(parent, "specter_state", None)

    menu_items = [("Manage Device", None)]

    if state and state.hasSD and state.enabledSD and state.detectedSD:
        menu_items.append((lv.SYMBOL.COPY + "Manage Backup(s)", "manage_backups"))

    if state and ((state.hasQR and state.enabledQR) or (state.hasSD and state.enabledSD and state.detectedSD) or (state.hasUSB and state.enabledUSB)):
        menu_items.append(("Manage Firmware", "manage_firmware"))    

    menu_items += [
        (lv.SYMBOL.BELL + " Manage Security Features", "manage_security"),
        ("Enable/Disable Interfaces", "interfaces"),
        (lv.SYMBOL.IMAGE + " Manage Display", "display_settings"),
        (lv.SYMBOL.VOLUME_MAX + " Manage Sounds", "sound_settings")
    ]

    menu_items += [
        (ORANGE + " " + lv.SYMBOL.WARNING + " Dangerzone#", None),
        (ORANGE + " " + lv.SYMBOL.LOOP + " Wipe Device#", "wipe_device")
    ]


    return GenericMenu("manage_device", "Manage Device/Storage", menu_items, parent, *args, **kwargs)
