from ..basic import GenericMenu
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv

class StorageMenu(GenericMenu):
    """Menu to manage storage devices (SD / SmartCard)."""

    TITLE_KEY = "MENU_MANAGE_STORAGE"

    def get_menu_items(self, t, state):
        menu_items = [(None, t("MENU_MANAGE_STORAGE"), None, None, None, None)]
        menu_items.append((BTC_ICONS.FILE, t("STORAGE_MENU_INTERNAL_FLASH"), "internal_flash", None, None, None))

        if state and state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard:
            menu_items.append((BTC_ICONS.SMARTCARD, t("STORAGE_MENU_SMARTCARD"), "smartcard", None, None, None))

        if state and state.hasSD and state.enabledSD and state.detectedSD:
            menu_items.append((BTC_ICONS.SD_CARD, t("STORAGE_MENU_SD_CARD"), "sdcard", None, None, None))

        return menu_items
