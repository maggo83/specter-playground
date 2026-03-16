from ..basic import GenericMenu
from ..basic.symbol_lib import BTC_ICONS

class AddWalletMenu(GenericMenu):
    """Menu to import or create a custom wallet/descriptor.

    The default/standard wallet is auto-created when a key is loaded,
    so no "Use Standard Wallet" option is needed here.

    menu_id: "add_wallet"
    """

    TITLE_KEY = "MENU_ADD_WALLET"

    def get_menu_items(self, t, state):
        menu_items = []

        # Import section
        menu_items.append((None, t("ADD_WALLET_IMPORT_FROM"), None, None, None, None))

        if state.QR_enabled():
            menu_items.append((BTC_ICONS.SCAN, t("HARDWARE_QR_CODE"), "import_from_qr", None, None, None))

        if state.SD_detected():
            menu_items.append((BTC_ICONS.SD_CARD, t("HARDWARE_SD_CARD"), "import_from_sd", None, None, None))

        # Customize section
        menu_items.append((None, t("ADD_WALLET_CUSTOMIZE"), None, None, None, None))
        menu_items.append((BTC_ICONS.CONSOLE, t("ADD_WALLET_CREATE_CUSTOM"), "create_custom_wallet", None, None, None))

        return menu_items
