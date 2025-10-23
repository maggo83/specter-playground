from .menu import GenericMenu
import lvgl as lv

from .symbol_lib import BTC_ICONS
from .ui_consts import GREEN_HEX, RED_HEX, WHITE_HEX


def MainMenu(parent, *args, **kwargs):
    # read state and navigation callback from the parent controller
    on_navigate = getattr(parent, "on_navigate", None)
    state = getattr(parent, "specter_state", None)

    menu_items = []

    #add "process inputs" label if any relevant input is available
    #relevant input possibilities are QR Scanner, SD Card, or (to sign messages) a registered wallet
    if (state and ((state.hasQR and state.enabledQR) 
                   or (state.hasSD and state.enabledSD and state.detectedSD) 
                   or (state.active_wallet and not state.active_wallet.isMultiSig)
                   or (state.active_wallet is None and state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard)
                   )):
        menu_items.append((None, "Process input", None, None))
        if (state.hasQR and state.enabledQR):
            menu_items.append((BTC_ICONS.SCAN, "Scan QR", "scan_qr", None))
        if (state.hasSD and state.enabledSD and state.detectedSD):
            menu_items.append((BTC_ICONS.SD_CARD, "Load File from SD", "load_sd", None))
        if (state and state.active_wallet and not state.active_wallet.isMultiSig):
            menu_items.append((BTC_ICONS.SIGN, "Sign Message", "sign_message", None))
        if (state and state.active_wallet is None and state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard):
            menu_items.append((BTC_ICONS.SEND, "Import Seed From SmartCard", "import_from_smartcard", None))

    menu_items.append((None, "Choose Wallet", None, None))
    if state.registered_wallets and len(state.registered_wallets) > 0:
        menu_items.append((BTC_ICONS.WALLET, "Change/Add Wallet", "change_wallet", None))
    else:
        menu_items.append((BTC_ICONS.PLUS, "Add Wallet", "add_wallet", None))

    menu_items.append((None, "Manage Settings", None, None))
    if (state and not state.active_wallet is None):
        menu_items.append((BTC_ICONS.WALLET, "Manage Wallet", "manage_wallet", None))

    menu_items.append((BTC_ICONS.GEAR, "Manage Device", "manage_device", None))
    menu_items.append((lv.SYMBOL.DRIVE, "Manage Storage", "manage_storage", None))


    return GenericMenu("main", "What do you want to do?", menu_items, parent, *args, **kwargs)
