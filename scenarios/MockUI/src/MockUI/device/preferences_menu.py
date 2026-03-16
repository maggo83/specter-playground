from ..basic import GenericMenu
from ..basic.symbol_lib import BTC_ICONS


class PreferencesMenu(GenericMenu):
    """Menu for UI preferences: display, sounds, tour restart."""

    TITLE_KEY = "MENU_MANAGE_PREFERENCES"

    def get_menu_items(self, t, state):
        return [
            (BTC_ICONS.PHOTO, t("DEVICE_MENU_DISPLAY"), "display_settings", None, None, None),
            (BTC_ICONS.BELL, t("DEVICE_MENU_SOUNDS"), "sound_settings", None, None, None),
            (BTC_ICONS.REFRESH, t("DEVICE_MENU_RESTART_TOUR"), "start_intro_tour", None, None, None),
        ]
