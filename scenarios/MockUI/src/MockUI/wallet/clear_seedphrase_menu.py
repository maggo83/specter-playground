from ..basic import RED_HEX, GenericMenu
from ..basic.symbol_lib import BTC_ICONS


class ClearSeedphraseMenu(GenericMenu):
    """Sub-menu for choosing where to clear the seedphrase from."""

    TITLE_KEY = "SEEDPHRASE_MENU_CLEAR_FROM"

    def get_menu_items(self, t, state):
        menu_items = []

        if state.SmartCard_hasSeed():
            menu_items.append((BTC_ICONS.SMARTCARD, t("HARDWARE_SMARTCARD"), "clear_from_smartcard", RED_HEX, None, None))
        if state.SD_hasSeed():
            menu_items.append((BTC_ICONS.SD_CARD, t("HARDWARE_SD_CARD"), "clear_from_sd", RED_HEX, None, None))
        menu_items.append((BTC_ICONS.FILE, t("HARDWARE_INTERNAL_FLASH"), "clear_from_flash", RED_HEX, None, None))
        menu_items.append((BTC_ICONS.TRASH, t("SEEDPHRASE_MENU_CLEAR_ALL"), "clear_all_storage", RED_HEX, None, None))

        return menu_items
