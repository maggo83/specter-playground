import lvgl as lv
from ..basic import GenericMenu
from ..basic.symbol_lib import BTC_ICONS


class LanguageMenu(GenericMenu):
    TITLE_KEY = "MENU_LANGUAGE"

    def get_menu_items(self, t, state):
        available_langs = self.i18n.get_available_languages()
        current_lang = self.i18n.get_language()

        menu_items = []

        for lang_code in available_langs:
            label = self.i18n.get_language_name(lang_code)
            # Add checkmark for currently selected language
            if lang_code == current_lang:
                symbol = BTC_ICONS.CHECK
            else:
                symbol = None

            # Pass a callback function instead of a string
            menu_items.append((symbol, label, lambda e, lc=lang_code: self._on_language_selected(e, lc), None, None, None))

        # Add "Load new language" option (uses default string navigation)
        menu_items.append((BTC_ICONS.RECEIVE, t("MENU_LOAD_NEW_LANGUAGE"), "load_language", None, None, None))

        return menu_items
    
    def _on_language_selected(self, e, lang_code):
        """Handle language selection: change language and go back."""
        if e.get_code() == lv.EVENT.CLICKED:
            self.gui.change_language(lang_code)
            self.on_navigate(None)
