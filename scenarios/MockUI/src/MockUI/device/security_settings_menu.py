from ..basic import RED_HEX, ORANGE, GenericMenu
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv


class SecuritySettingsMenu(GenericMenu):
    """Security hub: security features, firmware, backups, danger zone."""

    TITLE_KEY = "MENU_SETTINGS_SECURITY"

    def get_menu_items(self, t, state):
        menu_items = [
            (BTC_ICONS.SHIELD, t("MENU_MANAGE_SECURITY"), "manage_security_features", None, None, None),
            (BTC_ICONS.FLIP_HORIZONTAL, t("MENU_ENABLE_DISABLE_INTERFACES"), "interfaces", None, None, None),
        ]

        if state and ((state.hasQR and state.enabledQR) or (state.hasSD and state.enabledSD and state.detectedSD) or (state.hasUSB and state.enabledUSB)):
            menu_items.append((BTC_ICONS.CODE, t("MENU_MANAGE_FIRMWARE"), "manage_firmware", None, None, None))

        if state and state.hasSD and state.enabledSD and state.detectedSD:
            menu_items.append((BTC_ICONS.COPY, t("MENU_MANAGE_BACKUPS"), "manage_backups", None, None, None))

        menu_items += [
            (None, ORANGE + " " + lv.SYMBOL.WARNING + " " + t("DEVICE_MENU_DANGERZONE") + "#", None, None, None, None),
            (BTC_ICONS.ALERT_CIRCLE, t("DEVICE_MENU_WIPE"), "wipe_device", RED_HEX, None, "HELP_DEVICE_MENU_WIPE")
        ]

        return menu_items
