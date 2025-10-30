from ..basic import GenericMenu


def DeviceMenu(parent, *args, **kwargs):
    on_navigate = getattr(parent, "on_navigate", None)
    state = getattr(parent, "specter_state", None)

    menu_items = [("Manage Device", None)]

    if state and state.hasSD and state.enabledSD and state.detectedSD:
        menu_items.append(("Manage Backup(s)", "manage_backups"))

    if state and ((state.hasQR and state.enabledQR) or (state.hasSD and state.enabledSD and state.detectedSD) or (state.hasUSB and state.enabledUSB)):
        menu_items.append(("Manage Firmware", "manage_firmware"))    

    menu_items += [
        ("Manage Security Features", "manage_security"),
        ("Enable/Disable Interfaces", "interfaces"),
        ("Manage Display", "display_settings"),
        ("Manage Sounds", "sound_settings")
    ]

    menu_items += [
        ("Dangerzone", None),
        ("Wipe Device", "wipe_device")
    ]


    return GenericMenu("manage_device", "Manage Device/Storage", menu_items, parent, *args, **kwargs)
