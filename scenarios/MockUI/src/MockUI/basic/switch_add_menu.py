import lvgl as lv
from . import GenericMenu, BTN_HEIGHT, BTN_WIDTH
from .symbol_lib import BTC_ICONS


class SwitchAddMenu(GenericMenu):
    """Base class for any menu that elt's the user choose an active element from a list and optionally add a new element.
    E.g. switch/add MasterKeys and/or Wallets.

    Should never be used directly, only via subclasses.
    """

    def get_menu_items(self, t, state, elements, label_creation_cb, active_element, activation_cb, add_target_behavior=None, add_string=None):

        menu_items = []
        for item in elements:
            is_active = item is active_element
            menu_items.append((
                BTC_ICONS.CHECK if is_active and len(elements) > 1 else None,
                label_creation_cb(item),
                self._make_select_cb(activation_cb, item),
                None, None, None
            ))

        if add_string and add_target_behavior:
            menu_items.append((BTC_ICONS.PLUS, add_string, add_target_behavior, None, None, None))
            
        return menu_items

    def _make_select_cb(self, activation_cb, item):
        """Create callback that sets the active item and navigates back."""
        def cb(e):
            if e.get_code() == lv.EVENT.CLICKED:
                activation_cb(item)
                self.gui.refresh_ui()
                self.on_navigate(None)
        return cb