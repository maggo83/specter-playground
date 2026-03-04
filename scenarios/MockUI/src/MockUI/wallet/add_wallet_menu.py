from ..basic import GenericMenu
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv

class AddWalletMenu(GenericMenu):
    """Menu to create or import a wallet."""

    TITLE_KEY = "MENU_ADD_WALLET"

    def get_menu_items(self, t, state):
        menu_items = [
            (None, t("ADD_WALLET_NEW_SEEDPHRASE"), None, None, None, None),
            (BTC_ICONS.MNEMONIC, t("MENU_GENERATE_SEEDPHRASE"), "generate_seedphrase", None, None, None),
            (None, t("ADD_WALLET_IMPORT_FROM"), None, None, None, None),
        ]

        # Add SmartCard import if available
        if state and state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard:
            menu_items.append((BTC_ICONS.SMARTCARD, t("HARDWARE_SMARTCARD"), "import_from_smartcard", None, None, None))

        if state and state.hasQR and state.enabledQR:
            menu_items.append((BTC_ICONS.QR_CODE, t("HARDWARE_QR_CODE"), "import_from_qr", None, None, None))

        if state and state.hasSD and state.enabledSD and state.detectedSD:
            menu_items.append((BTC_ICONS.SD_CARD, t("HARDWARE_SD_CARD"), "import_from_sd", None, None, None))

        menu_items.append((BTC_ICONS.FILE, t("HARDWARE_INTERNAL_FLASH"), "import_from_flash", None, None, None))
        menu_items.append((lv.SYMBOL.KEYBOARD, t("ADD_WALLET_KEYBOARD"), "import_from_keyboard", None, None, None))

        return menu_items
