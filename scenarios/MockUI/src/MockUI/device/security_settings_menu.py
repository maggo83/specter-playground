from ..basic import RED_HEX, ORANGE, GenericMenu
from ..basic.symbol_lib import BTC_ICONS
from ..basic.widgets import MenuItem
import lvgl as lv

class SecuritySettingsMenu(GenericMenu):
    """Security hub: security features, firmware, backups, danger zone."""

    TITLE_KEY = "MENU_SETTINGS_SECURITY"

    def get_menu_items(self, t, state):
        menu_items = [
            MenuItem(BTC_ICONS.SHIELD, t("MENU_MANAGE_SECURITY"), "manage_security_features"),
            MenuItem(BTC_ICONS.FLIP_HORIZONTAL, t("MENU_ENABLE_DISABLE_INTERFACES"), "interfaces"),
        ]

        if state.SD_detected() or state.USB_enabled() or state.QR_enabled():
            menu_items.append(MenuItem(BTC_ICONS.CODE, t("MENU_MANAGE_FIRMWARE"), "manage_firmware"))

        if state.SD_detected():
            menu_items.append(MenuItem(BTC_ICONS.COPY, t("MENU_MANAGE_BACKUPS"), "manage_backups"))

        menu_items += [
            MenuItem(text=ORANGE + " " + lv.SYMBOL.WARNING + " " + t("DEVICE_MENU_DANGERZONE") + "#"),
            MenuItem(BTC_ICONS.ALERT_CIRCLE, t("DEVICE_MENU_WIPE"), "wipe_device", color=RED_HEX, help_key="HELP_DEVICE_MENU_WIPE"),
        ]

        return menu_items
