from ..basic import ORANGE_HEX, RED_HEX, GenericMenu
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv

class SeedPhraseMenu(GenericMenu):
    TITLE_KEY = "MENU_MANAGE_SEEDPHRASE"

    def get_menu_items(self, t, state):
        menu_items = []

        # Show the seedphrase (requires confirmation on a real device)
        menu_items.append((BTC_ICONS.VISIBLE, t("SEEDPHRASE_MENU_SHOW"), "show_seedphrase", ORANGE_HEX, None, None))

        # Storage sub-menus
        menu_items.append((None, t("SEEDPHRASE_MENU_STORAGE"), None, None, None, None))
        menu_items.append((lv.SYMBOL.DOWNLOAD, t("SEEDPHRASE_MENU_STORE_TO") + "...", "store_seedphrase", None, None, None))
        menu_items.append((BTC_ICONS.TRASH, t("SEEDPHRASE_MENU_CLEAR_FROM") + "...", "clear_seedphrase", RED_HEX, None, None))

        # Derive new via BIP-85
        menu_items.append((None, t("SEEDPHRASE_MENU_ADVANCED"), None, None, None, None))
        menu_items.append((BTC_ICONS.SHARED_WALLET, t("SEEDPHRASE_MENU_BIP85"), "derive_bip85", None, None, None))

        return menu_items
