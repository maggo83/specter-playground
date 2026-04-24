from ..basic import GenericMenu
from ..basic.symbol_lib import BTC_ICONS
from ..basic.widgets import MenuItem
from ..stubs import Seed

class ViewSignersScreen(GenericMenu):
    """Form to view the active seed's signers.

    menu_id: "view_signers"
    """

    TITLE_KEY = "WALLET_MENU_VIEW_SIGNERS"

    def get_menu_items(self, t, state):
        """Show list of signers for the active seed."""
        s4w = state.seeds_for_wallet(state.active_wallet)
        loaded_fp4w = Seed.get_fingerprints(s4w) if s4w else []

        menu_items = []
        for fp in state.active_wallet.required_fingerprints:
            signer_name = fp[2:]  # do not show "0x" hex prefix in fingerprint
            icon = None

            if s4w and fp in loaded_fp4w:
                signer_name += " (" + s4w[loaded_fp4w.index(fp)].label + ")"
                icon = BTC_ICONS.CHECK

            menu_items.append(MenuItem(icon, signer_name))
        return menu_items
    
    def post_init(self, t, state):
        """Add wallet name to title."""
        title = self.title.get_text()
        title += "," + state.active_wallet.label
        self.title.set_text(title)

