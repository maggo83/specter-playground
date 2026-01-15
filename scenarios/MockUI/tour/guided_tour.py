"""Guided tour for first-time users.

Provides a step-by-step introduction to the Specter hardware wallet UI,
highlighting key interface elements and explaining their purpose.
"""

from .ui_explainer import UIExplainer
from ..i18n.i18n_manager import t


class GuidedTour:
    """Manages the startup guided tour.
    
    The tour highlights key UI elements and provides explanations for new users.
    It runs once on first startup and can be dismissed or completed.
    
    Acts as the central controller - UIExplainer delegates navigation back here.
    
    Usage:
        tour = GuidedTour(nav_controller)
        tour.start()
    """
    
    def __init__(self, nav_controller):
        """Initialize the tour with a reference to the NavigationController.
        
        Args:
            nav_controller: The NavigationController instance (must be fully constructed)
        """
        self.nav = nav_controller
        self.steps = []
        self.current_index = 0
        self.current_explainer = None
    
    def start(self):
        """Build the steps list and show the first step."""
        db = self.nav.device_bar
        
        # Define tour steps: (element, text, position)
        # Element can be lv.obj reference, (x, y, w, h) tuple, or None
        self.steps = [
            (None, t("TOUR_INTRO"), "center"),
            (db.lang_lbl, t("TOUR_LANGUAGE"), "below"),
            (db.lock_btn, t("TOUR_LOCK"), "below"),
            (db.center_container, t("TOUR_INTERFACES"), "below"),
            (db.batt_icon, t("TOUR_BATTERY"), "below"),
            (db.power_btn, t("TOUR_POWER"), "below"),
            (self.nav.wallet_bar, t("TOUR_WALLET_BAR"), "above"),
            # Help icon: manual coordinates - approximate position for first help icon
            ((435, 143, 28, 28), t("TOUR_HELP_ICON"), "left"),
        ]
        
        self.current_index = 0
        self._show_current()
    
    def is_first(self):
        """Return True if currently on the first step."""
        return self.current_index == 0
    
    def is_last(self):
        """Return True if currently on the last step."""
        return self.current_index >= len(self.steps) - 1
    
    def prev(self):
        """Navigate to the previous step."""
        if not self.is_first():
            self.current_explainer.hide()
            self.current_index -= 1
            self._show_current()
    
    def next(self):
        """Navigate to the next step."""
        if not self.is_last():
            self.current_explainer.hide()
            self.current_index += 1
            self._show_current()
    
    def skip(self):
        """End the tour (skip or complete)."""
        self.current_explainer.hide()
        self.current_explainer = None
        self.nav.ui_state.set_tour_completed()
    
    def _show_current(self):
        """Show the current step."""
        element, text, position = self.steps[self.current_index]
        self.current_explainer = UIExplainer(self, element, text, position)
        self.current_explainer.show()
