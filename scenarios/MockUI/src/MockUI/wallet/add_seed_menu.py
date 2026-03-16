from ..basic import GenericMenu
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv


class AddSeedMenu(GenericMenu):
    """Menu to create or import a MasterKey (seedphrase).

    menu_id: "add_seed"
    """

    TITLE_KEY = "MENU_ADD_SEED"

    def get_menu_items(self, t, state):
        menu_items = []

        # Generate section
        menu_items.append((None, t("ADD_SEED_GENERATE_SECTION"), None, None, None, None))
        menu_items.append((BTC_ICONS.MNEMONIC, t("MAIN_MENU_GENERATE_SEED"), "generate_seedphrase", None, None, None))

        # Import section
        menu_items.append((None, t("ADD_SEED_IMPORT_SECTION"), None, None, None, None))

        # SmartCard (only when detected)
        if state.SmartCard_hasSeed():
            menu_items.append((BTC_ICONS.SMARTCARD, t("HARDWARE_SMARTCARD"), "import_from_smartcard", None, None, None))

        # QR Code
        if state.QR_enabled():
            menu_items.append((BTC_ICONS.SCAN, t("HARDWARE_QR_CODE"), "import_from_qr", None, None, None))

        # Keyboard (always available)
        menu_items.append((lv.SYMBOL.KEYBOARD, t("ADD_WALLET_KEYBOARD"), "import_from_keyboard", None, None, None))

        # SD Card (only if key data detected)
        if state.SD_hasSeed():
            menu_items.append((BTC_ICONS.SD_CARD, t("HARDWARE_SD_CARD"), "import_from_sd", None, None, None))

        # Internal Flash (only if key data detected)
        if state.Flash_hasSeed():
            menu_items.append((BTC_ICONS.FILE, t("HARDWARE_INTERNAL_FLASH"), "import_from_flash", None, None, None))

        return menu_items
