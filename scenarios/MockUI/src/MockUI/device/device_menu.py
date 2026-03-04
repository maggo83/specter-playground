from ..basic import RED_HEX, ORANGE, GenericMenu
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv


def DeviceMenu(parent):
    # Get translation function from i18n manager (always available via NavigationController)
    t = parent.i18n.t
    
    on_navigate = getattr(parent, "on_navigate", None)
    state = getattr(parent, "specter_state", None)

    menu_items = [(None, t("MENU_MANAGE_DEVICE"), None, None, None, None)]

    if state and state.hasSD and state.enabledSD and state.detectedSD:
        menu_items.append((BTC_ICONS.COPY, t("MENU_MANAGE_BACKUPS"), "manage_backups", None, None, None))

    if state and ((state.hasQR and state.enabledQR) or (state.hasSD and state.enabledSD and state.detectedSD) or (state.hasUSB and state.enabledUSB)):
        menu_items.append((BTC_ICONS.CODE, t("MENU_MANAGE_FIRMWARE"), "manage_firmware", None, None, None))

    menu_items += [
        (BTC_ICONS.SHIELD, t("MENU_MANAGE_SECURITY"), "manage_security", None, None, None),
        (BTC_ICONS.FLIP_HORIZONTAL, t("MENU_ENABLE_DISABLE_INTERFACES"), "interfaces", None, None, None),
        (BTC_ICONS.PHOTO, t("DEVICE_MENU_DISPLAY"), "display_settings", None, None, None),
        (lv.SYMBOL.VOLUME_MAX, t("DEVICE_MENU_SOUNDS"), "sound_settings", None, None, None),
        (BTC_ICONS.MESSAGE, t("MENU_LANGUAGE"), "select_language", None, None, None),
        (BTC_ICONS.REFRESH, t("DEVICE_MENU_RESTART_TOUR"), "start_intro_tour", None, None, None),
    ]

    menu_items += [
        (None, ORANGE + " " + lv.SYMBOL.WARNING+ " " + t("DEVICE_MENU_DANGERZONE") + "#", None, None, None, None),
        (BTC_ICONS.ALERT_CIRCLE, t("DEVICE_MENU_WIPE"), "wipe_device", RED_HEX, None, "HELP_DEVICE_MENU_WIPE")
    ]


    return GenericMenu(t("MENU_MANAGE_DEVICE"), menu_items, parent)
