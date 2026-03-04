from ..basic.menu import GenericMenu
import lvgl as lv

from ..basic.symbol_lib import BTC_ICONS


class SettingsMenu(GenericMenu):
    TITLE_KEY = "MENU_MANAGE_SETTINGS"

    def get_menu_items(self, t, state):
        menu_items = []

        # Device management
        menu_items.append((BTC_ICONS.GEAR, t("MENU_MANAGE_DEVICE"), "manage_device", None, None, None))

        # Storage management
        menu_items.append((lv.SYMBOL.DRIVE, t("MENU_MANAGE_STORAGE"), "manage_storage", None, None, None))

        return menu_items
