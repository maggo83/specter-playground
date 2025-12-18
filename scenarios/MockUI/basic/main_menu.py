from .menu import GenericMenu
import lvgl as lv

from .symbol_lib import BTC_ICONS
from .ui_consts import GREEN_HEX, RED_HEX, WHITE_HEX


def MainMenu(parent, *args, **kwargs):
    # read state and navigation callback from the parent controller
    on_navigate = getattr(parent, "on_navigate", None)
    state = getattr(parent, "specter_state", None)
    
    # Get translation function from i18n manager (always available via NavigationController)
    t = parent.i18n.t

    menu_items = []

    #add "process inputs" label if any relevant input is available
    #relevant input possibilities are QR Scanner, SD Card, or (to sign messages) a registered wallet
    if (state and ((state.hasQR and state.enabledQR) 
                   or (state.hasSD and state.enabledSD and state.detectedSD) 
                   or (state and state.active_wallet and not state.active_wallet.isMultiSig and 
                        (
                            (state.hasQR and state.enabledQR) 
                            or (state.hasSD and state.enabledSD and state.detectedSD)
                            or (state.hasUSB and state.enabledUSB)
                        ))
                   or (state.active_wallet is None and state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard)
                   )):
        menu_items.append((None, t("MAIN_MENU_PROCESS_INPUT"), None, None))
        if (state.hasQR and state.enabledQR):
            scan_size = 1
            if not (state.active_wallet is None):
                scan_size = 2
            menu_items.append((BTC_ICONS.SCAN, t("MAIN_MENU_SCAN_QR"), "scan_qr", None, scan_size))
        if (state.hasSD and state.enabledSD and state.detectedSD):
            menu_items.append((BTC_ICONS.SD_CARD, t("MAIN_MENU_LOAD_SD"), "load_sd", None, 2))
        if (state and state.active_wallet and not state.active_wallet.isMultiSig and 
            (
                   (state.hasQR and state.enabledQR) 
                or (state.hasSD and state.enabledSD and state.detectedSD)
                or (state.hasUSB and state.enabledUSB)
            )):
            menu_items.append((BTC_ICONS.SIGN, t("MAIN_MENU_SIGN_MESSAGE"), "sign_message", None))
        if (state and state.active_wallet is None and state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard):
            menu_items.append((BTC_ICONS.SEND, t("MAIN_MENU_IMPORT_SMARTCARD"), "import_from_smartcard", None, 2))

    menu_items.append((None, t("MAIN_MENU_CHOOSE_WALLET"), None, None))
    if state.registered_wallets and len(state.registered_wallets) > 0:
        menu_items.append((BTC_ICONS.WALLET, t("MAIN_MENU_CHANGE_ADD_WALLET"), "change_wallet", None))
    else:
        menu_items.append((BTC_ICONS.PLUS, t("MENU_ADD_WALLET"), "add_wallet", None, 2))

    menu_items.append((None, t("MAIN_MENU_MANAGE_SETTINGS"), None, None))
    if (state and not state.active_wallet is None):
        menu_items.append((BTC_ICONS.WALLET, t("MENU_MANAGE_WALLET"), "manage_wallet", None))

    menu_items.append((BTC_ICONS.GEAR, t("MENU_MANAGE_SETTINGS"), "manage_settings", None))


    return GenericMenu("main", t("MAIN_MENU_TITLE"), menu_items, parent, *args, **kwargs)
