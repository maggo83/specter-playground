from ..basic import GenericMenu
import lvgl as lv

class ConnectWalletsMenu(GenericMenu):
    """Menu to connect or export to software wallets."""

    TITLE_KEY = "MENU_CONNECT_SW_WALLET"

    def get_menu_items(self, t, state):
        return [
            (None, t("CONNECT_WALLETS_SPARROW"), "connect_sparrow", None, None, None),
            (None, t("CONNECT_WALLETS_NUNCHUCK"), "connect_nunchuck", None, None, None),
            (None, t("CONNECT_WALLETS_BLUEWALLET"), "connect_bluewallet", None, None, None),
            (None, t("CONNECT_WALLETS_OTHER"), "connect_other", None, None, None),
        ]
