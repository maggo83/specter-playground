from ..basic import SwitchAddMenu
from ..basic.widgets import MenuItem
from ..basic.symbol_lib import BTC_ICONS
from ..basic.ui_consts import WHITE_HEX, GREY_HEX, ORANGE_HEX


class SwitchAddSeedsMenu(SwitchAddMenu):
    """Switch/Add menu showing Seeds, grouped by wallet compatibility.

    When all loaded seeds are part of the active wallet, the list is shown flat
    (no section headers). When there are seeds that do *not* belong to the active
    wallet, the list is split into two labelled sections:
        1. "Seeds for active wallet"  — seeds that are signers for the active wallet
        2. "Other seeds"              — remaining loaded seeds
    """

    TITLE_KEY = "MENU_SWITCH_ADD_SEED"

    def _seed_suffix(self, seed):
        """Build right-side suffix info for a seed list item."""
        items = []
        if seed.passphrase is not None:
            pp_color = WHITE_HEX if seed.passphrase_active else GREY_HEX
            items.append((BTC_ICONS.PASSWORD, pp_color, None))
        if not seed.is_backed_up:
            items.append((BTC_ICONS.ALERT_CIRCLE, ORANGE_HEX, None))
        raw_fp = seed.fingerprint or "????"
        if raw_fp.startswith("0x") or raw_fp.startswith("0X"):
            raw_fp = raw_fp[2:]
        items.append((BTC_ICONS.RELAY, WHITE_HEX, raw_fp[:4]))
        return items

    def get_menu_items(self, t, state):
        wallet_seeds = self.state.seeds_for_wallet(state.active_wallet) or []
        other_seeds = [s for s in state.loaded_seeds if s not in wallet_seeds]
        show_check = len(wallet_seeds) + len(other_seeds) > 1

        def items(seeds, add_behavior=None, add_str=None):
            return super(SwitchAddSeedsMenu, self).get_menu_items(
                elements=seeds,
                label_creation_cb=lambda s: s.label,
                active_element=state.active_seed,
                activation_cb=self.state.set_active_seed,
                show_check=show_check,
                add_target_behavior=add_behavior,
                add_string=add_str,
                suffix_cb=self._seed_suffix,
            )

        if wallet_seeds:
            if other_seeds:
                return (
                    [MenuItem(text=t("ADD_SWITCH_SEED_MENU_SEEDS_FOR_WALLET"))]
                    + items(wallet_seeds)
                    + [MenuItem(text=t("ADD_SWITCH_SEED_MENU_OTHER_SEEDS"))]
                    + items(other_seeds, "add_seed", t("MENU_ADD_SEED"))
                )
            else:
                return items(wallet_seeds, "add_seed", t("MENU_ADD_SEED"))
        else:
            if other_seeds:
                return items(other_seeds, "add_seed", t("MENU_ADD_SEED"))
            else:
                return []
        