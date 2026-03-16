from ..basic import SwitchAddMenu

class SwitchAddSeedsMenu(SwitchAddMenu):
    """Switch/Add menu showing only Seeds."""
    TITLE_KEY = "MENU_SWITCH_ADD_SEED"

    def get_menu_items(self, t, state):
        return super().get_menu_items(
            t, state,
            elements=state.loaded_seeds,
            label_creation_cb=lambda seed: seed.label,
            active_element=state.active_seed,
            activation_cb= lambda seed: self.state.set_active_seed(seed),
            add_target_behavior="add_seed",
            add_string=t("MENU_ADD_SEED")
        )