from ..basic import SwitchAddMenu
from ..basic.symbol_lib import BTC_ICONS


class SwitchAddWalletsMenu(SwitchAddMenu):
    """Switch/Add menu showing Wallets, grouped by seed compatibility.

    When all registered wallets are compatible with the active seed, the list is
    shown flat (no section headers)
    When there are wallets that do *not* match the active seed, the list is split into two labelled sections:
        1. "Wallets for active seed"  — wallets usable with the currently loaded seed
        2. "Other wallets"            — remaining registered wallets
    """

    TITLE_KEY = "MENU_SWITCH_ADD_WALLET"

    def _create_wallet_items(self, wallets, active_wallet):
        """Return menu item tuples for a list of wallets."""
        items = []
        for wallet in wallets:
            icon = BTC_ICONS.CHECK if wallet is active_wallet else None
            items.append((icon, wallet.label, self._make_select_cb(self.state.set_active_wallet, wallet), None, None, None))
        return items

    def get_menu_items(self, t, state):
        seed_wallets = self.state.wallets_for_seed(state.active_seed) or []
        other_wallets = [w for w in state.registered_wallets if w not in seed_wallets]
        has_other = len(other_wallets) > 0

        menu_items = []

        # ── Section 1: wallets compatible with the active seed ──────────────
        if has_other:
            menu_items.append((None, t("ADD_SWITCH_WALLET_MENU_WALLETS_FOR_SEED"), None, None, None, None))
        menu_items.extend(self._create_wallet_items(seed_wallets, state.active_wallet))

        # ── Section 2: wallets that do not match the active seed ────────────
        if has_other:
            menu_items.append((None, t("ADD_SWITCH_WALLET_MENU_OTHER_WALLETS"), None, None, None, None))
            menu_items.extend(self._create_wallet_items(other_wallets, state.active_wallet))

        # ── Always: "Add Wallet" action at the bottom ───────────────────────
        menu_items.append((BTC_ICONS.PLUS, t("MENU_ADD_WALLET"), "add_wallet", None, None, None))
        return menu_items