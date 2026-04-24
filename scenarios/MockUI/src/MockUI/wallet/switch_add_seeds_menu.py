from ..basic import SwitchAddMenu
from ..basic.widgets import MenuItem


class SwitchAddSeedsMenu(SwitchAddMenu):
    """Switch/Add menu showing Seeds, grouped by wallet compatibility.

    When all loaded seeds are part of the active wallet, the list is shown flat
    (no section headers). When there are seeds that do *not* belong to the active
    wallet, the list is split into two labelled sections:
        1. "Seeds for active wallet"  — seeds that are signers for the active wallet
        2. "Other seeds"              — remaining loaded seeds
    """

    TITLE_KEY = "MENU_SWITCH_ADD_SEED"

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
        