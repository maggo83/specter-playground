from ..basic import GenericMenu
import lvgl as lv

class ConnectWalletsMenu(GenericMenu):
    """Menu to connect or export to software wallets.

    Selecting any companion app marks the active wallet as exported,
    since the descriptor is being shared with that app.
    """

    TITLE_KEY = "MENU_CONNECT_SW_WALLET"

    def get_menu_items(self, t, state):
        return [
            (None, t("CONNECT_WALLETS_SPARROW"),
             self._mark_exported_and_navigate("connect_sparrow"), None, None, None),
            (None, t("CONNECT_WALLETS_NUNCHUCK"),
             self._mark_exported_and_navigate("connect_nunchuck"), None, None, None),
            (None, t("CONNECT_WALLETS_BLUEWALLET"),
             self._mark_exported_and_navigate("connect_bluewallet"), None, None, None),
            (None, t("CONNECT_WALLETS_OTHER"),
             self._mark_exported_and_navigate("connect_other"), None, None, None),
        ]

    def _mark_exported_and_navigate(self, target):
        """Return a callback that sets has_been_exported then navigates."""
        def _cb(e):
            if e.get_code() != lv.EVENT.CLICKED:
                return
            self.state.active_wallet.has_been_exported = True
            self.gui.show_menu(None)
        return _cb