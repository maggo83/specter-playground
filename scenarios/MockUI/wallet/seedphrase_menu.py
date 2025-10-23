from ..basic import ORANGE, ORANGE_HEX, RED_HEX, GenericMenu
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv

def SeedPhraseMenu(parent, *args, **kwargs):
    on_navigate = getattr(parent, "on_navigate", None)
    state = getattr(parent, "specter_state", None)

    menu_items = []

    # Show the seedphrase (requires confirmation in a real device)
    menu_items.append((BTC_ICONS.VISIBLE, "Show Seedphrase", "show_seedphrase", ORANGE_HEX))

    # Store Seedphrase group (label)
    menu_items.append((None, lv.SYMBOL.DOWNLOAD + " Store Seedphrase", None, None))
    if state and state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard:
        menu_items.append((BTC_ICONS.SMARTCARD, "to SmartCard", "store_to_smartcard", None))
    if state and state.hasSD and state.enabledSD and state.detectedSD:
        menu_items.append((BTC_ICONS.SD_CARD, "to SD Card", "store_to_sd", None))
    menu_items.append((BTC_ICONS.FILE, "to internal Flash", "store_to_flash", None))

    # Clear Seedphrase group (label)
    menu_items.append((None, ORANGE + " " + lv.SYMBOL.CLOSE + " Clear Seedphrase#", None, None))
    if state and state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard:
        menu_items.append((BTC_ICONS.SMARTCARD, "from SmartCard", "clear_from_smartcard", RED_HEX))
    if state and state.hasSD and state.enabledSD and state.detectedSD:
        menu_items.append((BTC_ICONS.SD_CARD, "from SD Card", "clear_from_sd", RED_HEX))
    menu_items.append((BTC_ICONS.FILE, "from internal Flash", "clear_from_flash", RED_HEX))
    menu_items.append((BTC_ICONS.TRASH, "all attached storage", "clear_all_storage", RED_HEX))

    # Derive new via BIP-85
    menu_items.append((None, "Advanced Features", None, None))
    menu_items.append((BTC_ICONS.SHARED_WALLET, "Derive new via BIP-85", "derive_bip85", None))

    return GenericMenu("manage_seedphrase", "Manage Seedphrase", menu_items, parent, *args, **kwargs)
