from ..basic import SwitchAddMenu


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
        common = dict(
            label_creation_cb=lambda s: s.label,
            active_element=state.active_seed,
            activation_cb=self.state.set_active_seed,
            show_check=len(wallet_seeds) + len(other_seeds) > 1,
        )

        if not other_seeds:
            return super().get_menu_items(
                t, state, elements=wallet_seeds, **common,
                add_target_behavior="add_seed", add_string=t("MENU_ADD_SEED"),
            )

        return (
            [(None, t("ADD_SWITCH_SEED_MENU_SEEDS_FOR_WALLET"), None, None, None, None)]
            + super().get_menu_items(t, state, elements=wallet_seeds, **common)
            + [(None, t("ADD_SWITCH_SEED_MENU_OTHER_SEEDS"), None, None, None, None)]
            + super().get_menu_items(
                t, state, elements=other_seeds, **common,
                add_target_behavior="add_seed", add_string=t("MENU_ADD_SEED"),
            )
        )