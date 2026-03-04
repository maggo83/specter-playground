from ..basic import GenericMenu
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv

class SecurityMenu(GenericMenu):
    TITLE_KEY = "MENU_MANAGE_SECURITY"

    def get_menu_items(self, t, state):
        return [
            (BTC_ICONS.PASSWORD, t("SECURITY_MENU_CHANGE_PIN"), "change_pin", None, None, None),
            (BTC_ICONS.CHECK, t("SECURITY_MENU_SELF_TEST"), "self_test", None, None, None),
            (None, t("SECURITY_MENU_PIN_RETRIES"), "set_allowed_pin_retries", None, None, None),
            (None, t("SECURITY_MENU_PIN_ACTION"), "set_exceeded_pin_action", None, None, None),
            (None, t("SECURITY_MENU_DURESS_PIN"), "set_duress_pin", None, None, None),
            (None, t("SECURITY_MENU_DURESS_ACTION"), "set_duress_pin_action", None, None, None),
        ]
