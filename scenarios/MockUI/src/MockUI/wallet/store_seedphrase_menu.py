from ..basic import GenericMenu, ORANGE_HEX
from ..basic.symbol_lib import BTC_ICONS


class StoreSeedphraseMenu(GenericMenu):
    """Sub-menu for choosing where to store the seedphrase."""

    TITLE_KEY = "SEEDPHRASE_MENU_STORE_TO"

    def get_menu_items(self, t, state):
        menu_items = []

        if state.SmartCard_detected():
            menu_items.append((BTC_ICONS.SMARTCARD, t("HARDWARE_SMARTCARD"), "store_to_smartcard", None, None, None))
        if state.SD_detected():
            menu_items.append((BTC_ICONS.SD_CARD, t("HARDWARE_SD_CARD"), "store_to_sd", None, None, None))
        menu_items.append((BTC_ICONS.FILE, t("HARDWARE_INTERNAL_FLASH"), "store_to_flash", ORANGE_HEX, None, None))

        return menu_items
