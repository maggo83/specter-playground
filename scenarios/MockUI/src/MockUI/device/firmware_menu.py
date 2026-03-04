from ..basic import GenericMenu
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv


class FirmwareMenu(GenericMenu):
    """Menu for firmware management."""

    TITLE_KEY = "MENU_MANAGE_FIRMWARE"

    def get_menu_items(self, t, state):
        fw_version = state.fw_version

        menu_items = [
            (None, t("FIRMWARE_MENU_CURRENT_VERSION") + str(fw_version) + t("FIRMWARE_MENU_UPDATE_VIA"), None, None, None, None),
        ]

        if state and getattr(state, 'hasSD', False) and getattr(state, 'enabledSD', False) and getattr(state, 'detectedSD', False):
            menu_items.append((BTC_ICONS.SD_CARD, t("HARDWARE_SD_CARD"), "update_fw_sd", None, None, None))

        if state and getattr(state, 'hasUSB', False) and getattr(state, 'enabledUSB', False):
            menu_items.append((BTC_ICONS.USB, t("HARDWARE_USB"), "update_fw_usb", None, None, None))

        if state and getattr(state, 'hasQR', False) and getattr(state, 'enabledQR', False):
            menu_items.append((BTC_ICONS.QR_CODE, t("HARDWARE_QR_CODE"), "update_fw_qr", None, None, None))

        return menu_items
