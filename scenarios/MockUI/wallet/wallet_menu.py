from ..basic import RED_HEX, GenericMenu, RED, ORANGE
import lvgl as lv

def WalletMenu(parent, *args, **kwargs):
    on_navigate = getattr(parent, "on_navigate", None)
    state = getattr(parent, "specter_state", None)

    menu_items = []

    menu_items.append((None, "Explore", None, None))
    menu_items.append((lv.SYMBOL.EYE_OPEN, "View Addresses", "view_addresses", None))
    if (state and not state.active_wallet is None and state.active_wallet.isMultiSig):
        menu_items.append((None, "View Signers", "view_signers", None))

    menu_items.append((None, "Manage", None, None))
    if (state and not state.active_wallet is None and not state.active_wallet.isMultiSig):
        #Probably not needed as a fixed setting -> derivation path can be chosen in address explorer or when exporting public keys
        #menu_items.append((None, "Manage Derivation Path", "derivation_path", None))
        menu_items.append((None, "Manage Seedphrase", "manage_seedphrase", None))
        menu_items.append((lv.SYMBOL.NEW_LINE, "Enter/Set Passphrase", "set_passphrase", None))
    elif (state and not state.active_wallet is None and state.active_wallet.isMultiSig):
        menu_items.append((None, "Manage Descriptor", "manage_wallet_descriptor", None))
    menu_items.append((None, "Change Network (Mainnet/Testnet...)", "change_network", None))

    menu_items += [
        (lv.SYMBOL.EDIT, "Rename Wallet", "rename_wallet", None),
        (lv.SYMBOL.TRASH, "Delete Wallet#", "delete_wallet", RED_HEX),
        (None, "Connect/Export", None, None),
        (lv.SYMBOL.REFRESH, "Connect SW Wallet", "connect_sw_wallet", None),
        (lv.SYMBOL.UPLOAD, "Export Data", "export_wallet", None)
    ]

    title = "Manage Wallet" + ("" if state is None or state.active_wallet is None else f": {state.active_wallet.name}")

    return GenericMenu("manage_wallet", title, menu_items, parent, *args, **kwargs)
