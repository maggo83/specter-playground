from ..basic import GenericMenu
from ..basic.symbol_lib import BTC_ICONS

class StorageMenu(GenericMenu):
    """Menu to manage storage devices (SD / SmartCard)."""

    TITLE_KEY = "MENU_MANAGE_STORAGE"

    def get_menu_items(self, t, state):
        menu_items = []
        menu_items.append((BTC_ICONS.FILE, t("STORAGE_MENU_INTERNAL_FLASH"), "internal_flash", None, None, None))

        if state.SmartCard_detected():
            menu_items.append((BTC_ICONS.SMARTCARD, t("STORAGE_MENU_SMARTCARD"), "smartcard", None, None, None))

        if state.SD_detected():
            menu_items.append((BTC_ICONS.SD_CARD, t("STORAGE_MENU_SD_CARD"), "sdcard", None, None, None))
            menu_items.append((BTC_ICONS.COPY, t("MENU_MANAGE_BACKUPS"), "manage_backups", None, None, None))

        return menu_items
