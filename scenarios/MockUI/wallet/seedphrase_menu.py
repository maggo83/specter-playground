from ..basic import GenericMenu
import lvgl as lv


def SeedPhraseMenu(parent, *args, **kwargs):
    on_navigate = getattr(parent, "on_navigate", None)
    state = getattr(parent, "specter_state", None)

    menu_items = []

    # Show the seedphrase (requires confirmation in a real device)
    menu_items.append((lv.SYMBOL.EYE_OPEN, "Show Seedphrase", "show_seedphrase"))

    # Store Seedphrase group (label)
    menu_items.append((None, lv.SYMBOL.DOWNLOAD + " Store Seedphrase", None))
    if state and state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard:
        menu_items.append((None, "to SmartCard", "store_to_smartcard"))
    if state and state.hasSD and state.enabledSD and state.detectedSD:
        menu_items.append((lv.SYMBOL.SD_CARD, "to SD Card", "store_to_sd"))
    menu_items.append((lv.SYMBOL.DIRECTORY, "to internal Flash", "store_to_flash"))

    # Clear Seedphrase group (label)
    menu_items.append((None, lv.SYMBOL.CLOSE + " Clear Seedphrase", None))
    if state and state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard:
        menu_items.append((None, "from SmartCard", "clear_from_smartcard"))
    if state and state.hasSD and state.enabledSD and state.detectedSD:
        menu_items.append((lv.SYMBOL.SD_CARD, "from SD Card", "clear_from_sd"))
    menu_items.append((lv.SYMBOL.DIRECTORY, "from internal Flash", "clear_from_flash"))
    menu_items.append((None, "all attached storage", "clear_all_storage"))

    # Derive new via BIP-85
    menu_items.append((None, "Advanced Features", None))
    menu_items.append((None, "Derive new via BIP-85", "derive_bip85"))

    return GenericMenu("manage_seedphrase", "Manage Seedphrase", menu_items, parent, *args, **kwargs)
