from .menu import GenericMenu
import lvgl as lv


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
        menu_items.append(("Process input", None))
        if (state.hasQR and state.enabledQR):
            menu_items.append(("Scan QR", "scan_qr"))
        if (state.hasSD and state.enabledSD and state.detectedSD):
            menu_items.append((lv.SYMBOL.SD_CARD+" Load File from SD", "load_sd"))
        if (state and state.active_wallet and not state.active_wallet.isMultiSig):
            menu_items.append((lv.SYMBOL.EDIT+" Sign Message", "sign_message"))
        if (state and state.active_wallet is None and state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard):
            menu_items.append((lv.SYMBOL.UPLOAD+" Import Seed From SmartCard", "import_from_smartcard"))

    menu_items.append(("Manage Settings", None))
    if (state and not state.active_wallet is None):
        menu_items.append(("Manage Wallet", "manage_wallet"))

    menu_items.append((lv.SYMBOL.SETTINGS+" Manage Device", "manage_device"))
    # expose a dedicated Manage Storage entry when any storage device is present
    if state and ((state.hasSD and state.enabledSD and state.detectedSD) or (state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard)):
        menu_items.append((lv.SYMBOL.DRIVE+" Manage Storage", "manage_storage"))
    if state.registered_wallets and len(state.registered_wallets) > 0:
        menu_items.append(("Change/Add Wallet", "change_wallet"))
    else:
        menu_items.append((lv.SYMBOL.PLUS+" Add Wallet", "add_wallet"))


    return GenericMenu("main", lv.SYMBOL.HOME+" What do you want to do?", menu_items, parent, *args, **kwargs)
