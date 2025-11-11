from ..basic import RED_HEX, GenericMenu, RED, ORANGE
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv

def WalletMenu(parent, *args, **kwargs):
    on_navigate = getattr(parent, "on_navigate", None)
    state = getattr(parent, "specter_state", None)

    menu_items = []

    menu_items.append((None, "Explore", None, None))
    menu_items.append((BTC_ICONS.MENU, "View Addresses", "view_addresses", None))
    if (state and not state.active_wallet is None and state.active_wallet.isMultiSig):
        menu_items.append((BTC_ICONS.CONTACTS, "View Signers", "view_signers", None))

    menu_items.append((None, "Manage", None, None))
    if (state and not state.active_wallet is None and not state.active_wallet.isMultiSig):
        #Probably not needed as a fixed setting -> derivation path can be chosen in address explorer or when exporting public keys
        #menu_items.append((None, "Manage Derivation Path", "derivation_path", None))
        menu_items.append((BTC_ICONS.MNEMONIC, "Manage Seedphrase", "manage_seedphrase", None))
        menu_items.append((BTC_ICONS.PASSWORD, "Enter/Set Passphrase", "set_passphrase", None))
    elif (state and not state.active_wallet is None and state.active_wallet.isMultiSig):
        menu_items.append((BTC_ICONS.CONSOLE, "Manage Descriptor", "manage_wallet_descriptor", None))
    menu_items.append((BTC_ICONS.BITCOIN, "Change Network", "change_network", None))

    menu_items += [
        (BTC_ICONS.EDIT, "Rename Wallet", "rename_wallet", None),
        (BTC_ICONS.TRASH, "Delete Wallet#", "delete_wallet", RED_HEX),
        (None, "Connect/Export", None, None),
        (BTC_ICONS.LINK, "Connect SW Wallet", "connect_sw_wallet", None),
        (BTC_ICONS.EXPORT, "Export Data", "export_wallet", None)
    ]

    title = "Manage Wallet" + ("" if state is None or state.active_wallet is None else f": {state.active_wallet.name}")

    return GenericMenu("manage_wallet", title, menu_items, parent, *args, **kwargs)
