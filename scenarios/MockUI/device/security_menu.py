from ..basic import GenericMenu
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv

def SecurityMenu(parent, *args, **kwargs):
    state = getattr(parent, "specter_state", None)

    menu_items = [
        (BTC_ICONS.PASSWORD, "Change PIN", "change_pin", None),
        (BTC_ICONS.CHECK, "Run Self-Test", "self_test", None),
        (None, "Set allowed PIN retries", "set_allowed_pin_retries", None),
        (None, "Set exceeded PIN retries action", "set_exceeded_pin_action", None),
        (None, "Set duress PIN", "set_duress_pin", None),
        (None, "Set duress PIN action", "set_duress_pin_action", None),
    ]

    return GenericMenu("manage_security", lv.SYMBOL.BELL + " Manage Security Features", menu_items, parent, *args, **kwargs)
