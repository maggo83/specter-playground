from ..basic import SwitchAddMenu
from ..basic.symbol_lib import BTC_ICONS


class SwitchAddSeedsMenu(SwitchAddMenu):
    """Switch/Add menu showing Seeds, grouped by wallet compatibility.

    When all loaded seeds are part of the active wallet, the list is shown flat
    (no section headers). When there are seeds that do *not* belong to the active
    wallet, the list is split into two labelled sections:
        1. "Seeds for active wallet"  — seeds that are signers for the active wallet
        2. "Other seeds"              — remaining loaded seeds
    """

    TITLE_KEY = "MENU_SWITCH_ADD_SEED"

    def _create_seed_items(self, seeds, active_seed):
        """Return menu item tuples for a list of seeds."""
        items = []
        for seed in seeds:
            icon = BTC_ICONS.CHECK if seed is active_seed else None
            items.append((icon, seed.label, self._make_select_cb(self.state.set_active_seed, seed), None, None, None))
        return items

    def get_menu_items(self, t, state):
        wallet_seeds = self.state.seeds_for_wallet(state.active_wallet) or []
        other_seeds = [s for s in state.loaded_seeds if s not in wallet_seeds]
        has_other = len(other_seeds) > 0

        menu_items = []

        # ── Section 1: seeds that are part of the active wallet ─────────────
        if has_other:
            menu_items.append((None, t("ADD_SWITCH_SEED_MENU_SEEDS_FOR_WALLET"), None, None, None, None))
        menu_items.extend(self._create_seed_items(wallet_seeds, state.active_seed))

        # ── Section 2: seeds not part of the active wallet ──────────────────
        if has_other:
            menu_items.append((None, t("ADD_SWITCH_SEED_MENU_OTHER_SEEDS"), None, None, None, None))
            menu_items.extend(self._create_seed_items(other_seeds, state.active_seed))

        # ── Always: "Add Seed" action at the bottom ─────────────────────────
        menu_items.append((BTC_ICONS.PLUS, t("MENU_ADD_SEED"), "add_seed", None, None, None))
        return menu_items