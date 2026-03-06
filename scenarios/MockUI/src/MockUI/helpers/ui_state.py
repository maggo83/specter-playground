"""Runtime-friendly UI state helper for the MockUI.

Keeps track of the UI-specific state in a small, mutable object so the
navigation controller and menus can be kept stateless and simple.

Designed to avoid typing and external deps so it runs in the MicroPython
simulator environment.
"""

import json


CONFIG_FILE = "/flash/ui_state_config.json"


class UIState:
    """Small helper to track UI-level state.

    Attributes are intentionally public and mutable for simplicity in the
    mock environment.
    """

    def __init__(self):
        # current visible menu id (string)
        self.current_menu_id = "main"

        # stack of previous menu ids (LIFO)
        self.history = []

        # modal currently open (string name) or None
        self.modal = None

        # Tour state - loaded from config file
        self._run_tour_on_startup = self._load_tour_state()

    @property
    def run_tour_on_startup(self):
        """Whether the guided tour should run on startup."""
        return self._run_tour_on_startup
    
    def set_tour_completed(self):
        """Mark the tour as completed and persist the state."""
        self._run_tour_on_startup = False
        self._save_tour_state()
    
    def reset_tour(self):
        """Reset tour state to run again on next startup (for testing)."""
        self._run_tour_on_startup = True
        self._save_tour_state()
    
    def _load_tour_state(self):
        """Load tour completion state from config file."""
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return not config.get("tour_completed", False)
        except OSError:
            # File doesn't exist - first run, show tour
            return True
    
    def _save_tour_state(self):
        """Save tour completion state to config file."""
        config = {"tour_completed": not self._run_tour_on_startup}
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

    # Navigation helpers
    def push_menu(self, menu_id):
        """Navigate to a new menu and push the old one on the history stack."""
        if self.current_menu_id is not None:
            self.history.append(self.current_menu_id)
        self.current_menu_id = menu_id

    def pop_menu(self):
        """Pop the last menu from history and make it current (or go to 'main')."""
        if self.history:
            self.current_menu_id = self.history.pop()
        else:
            self.current_menu_id = "main"

    def clear_history(self):
        self.history.clear()
    # Modal helpers
    def open_modal(self, name):
        self.modal = name

    def close_modal(self):
        self.modal = None

    def is_modal_open(self):
        return self.modal is not None
