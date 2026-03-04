from ..basic import ORANGE, ORANGE_HEX, RED_HEX, GenericMenu
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv

class SeedPhraseMenu(GenericMenu):
    TITLE_KEY = "MENU_MANAGE_SEEDPHRASE"

    def get_menu_items(self, t, state):
        menu_items = []

        # Show the seedphrase (requires confirmation in a real device)
        menu_items.append((BTC_ICONS.VISIBLE, t("SEEDPHRASE_MENU_SHOW"), "show_seedphrase", ORANGE_HEX, None, None))

        # Store Seedphrase group (label)
        menu_items.append((None, lv.SYMBOL.DOWNLOAD + " " + t("SEEDPHRASE_MENU_STORE_TO"), None, None, None, None))
        if state and state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard:
            menu_items.append((BTC_ICONS.SMARTCARD, t("HARDWARE_SMARTCARD"), "store_to_smartcard", None, None, None))
        if state and state.hasSD and state.enabledSD and state.detectedSD:
            menu_items.append((BTC_ICONS.SD_CARD, t("HARDWARE_SD_CARD"), "store_to_sd", None, None, None))
        menu_items.append((BTC_ICONS.FILE, t("HARDWARE_INTERNAL_FLASH"), "store_to_flash", None, None, None))

        # Clear Seedphrase group (label)
        menu_items.append((None, ORANGE + " " + lv.SYMBOL.CLOSE + " " + t("SEEDPHRASE_MENU_CLEAR_FROM") + "#", None, None, None, None))
        if state and state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard:
            menu_items.append((BTC_ICONS.SMARTCARD, t("HARDWARE_SMARTCARD"), "clear_from_smartcard", RED_HEX, None, None))
        if state and state.hasSD and state.enabledSD and state.detectedSD:
            menu_items.append((BTC_ICONS.SD_CARD, t("HARDWARE_SD_CARD"), "clear_from_sd", RED_HEX, None, None))
        menu_items.append((BTC_ICONS.FILE, t("HARDWARE_INTERNAL_FLASH"), "clear_from_flash", RED_HEX, None, None))
        menu_items.append((BTC_ICONS.TRASH, t("SEEDPHRASE_MENU_CLEAR_ALL"), "clear_all_storage", RED_HEX, None, None))

        # Derive new via BIP-85
        menu_items.append((None, t("SEEDPHRASE_MENU_ADVANCED"), None, None, None, None))
        menu_items.append((BTC_ICONS.SHARED_WALLET, t("SEEDPHRASE_MENU_BIP85"), "derive_bip85", None, None, None))

        return menu_items
