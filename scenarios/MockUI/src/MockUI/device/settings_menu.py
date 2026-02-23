from ..basic.menu import GenericMenu
import lvgl as lv

from ..basic.symbol_lib import BTC_ICONS


def SettingsMenu(parent, *args, **kwargs):
    # read state and navigation callback from the parent controller
    on_navigate = getattr(parent, "on_navigate", None)
    state = getattr(parent, "specter_state", None)
    
    # Get translation function from i18n manager (always available via NavigationController)
    t = parent.i18n.t

    menu_items = []

    # Device management
    menu_items.append((BTC_ICONS.GEAR, t("MENU_MANAGE_DEVICE"), "manage_device", None, None, None))
    
    # Storage management
    menu_items.append((lv.SYMBOL.DRIVE, t("MENU_MANAGE_STORAGE"), "manage_storage", None, None, None))

    return GenericMenu("manage_settings", t("MENU_MANAGE_SETTINGS"), menu_items, parent, *args, **kwargs)
