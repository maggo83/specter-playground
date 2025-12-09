from ..basic import GenericMenu
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv


class FirmwareMenu(GenericMenu):
    """Menu for firmware management.

    menu_id: "manage_firmware"
    """

    def __init__(self, parent, *args, **kwargs):
        state = parent.specter_state

        # menu items (firmware version will be shown separately as a small label)
        # support either `fw_version` or `firmware_version` on the state object
        fw_version = state.fw_version

        menu_items = [
            (None, "Current version " + str(fw_version) + ". Update via", None, None),
        ]

        # conditional sources (guard against missing attributes)
        if state and getattr(state, 'hasSD', False) and getattr(state, 'enabledSD', False) and getattr(state, 'detectedSD', False):
            menu_items.append((BTC_ICONS.SD_CARD, "SD Card", "update_fw_sd", None))

        if state and getattr(state, 'hasUSB', False) and getattr(state, 'enabledUSB', False):
            menu_items.append((BTC_ICONS.USB, "USB", "update_fw_usb", None))

        if state and getattr(state, 'hasQR', False) and getattr(state, 'enabledQR', False):
            menu_items.append((BTC_ICONS.QR_CODE, "QR", "update_fw_qr", None))


        title = "Manage Firmware"
        super().__init__("manage_firmware", title, menu_items, parent, *args, **kwargs)
