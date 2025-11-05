from ..basic import GenericMenu
import lvgl as lv

def SecurityMenu(parent, *args, **kwargs):
    state = getattr(parent, "specter_state", None)

    menu_items = [
        (None, "Change PIN", "change_pin"),
        (None, "Run Self-Test", "self_test"),
        (None, "Set allowed PIN retries", "set_allowed_pin_retries"),
        (None, "Set exceeded PIN retries action", "set_exceeded_pin_action"),
        (None, "Set duress PIN", "set_duress_pin"),
        (None, "Set duress PIN action", "set_duress_pin_action"),
    ]

    return GenericMenu("manage_security", lv.SYMBOL.BELL + " Manage Security Features", menu_items, parent, *args, **kwargs)
