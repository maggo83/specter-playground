from ..basic.menu import GenericMenu
import lvgl as lv

from ..basic.symbol_lib import BTC_ICONS


class SettingsMenu(GenericMenu):
    TITLE_KEY = "MENU_MANAGE_SETTINGS"

    def get_menu_items(self, t, state):
        # Show current language code inline on the Language button
        lang_code = self.parent.i18n.get_language()
        lang_label = t("MENU_LANGUAGE") + " (" + lang_code.upper() + ")"

        return [
            (BTC_ICONS.SHIELD, t("MENU_SETTINGS_SECURITY"), "manage_security_settings", None, None, None),
            (BTC_ICONS.FILE, t("MENU_MANAGE_STORAGE"), "manage_storage", None, None, None),
            (BTC_ICONS.CONTACTS, t("MENU_MANAGE_PREFERENCES"), "manage_preferences", None, None, None),
            (BTC_ICONS.GLOBE, lang_label, "select_language", None, None, None),
        ]
