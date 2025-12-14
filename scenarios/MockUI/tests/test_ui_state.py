"""Tests for UIState."""
from MockUI.helpers.ui_state import UIState


class TestUIStateInit:
    def test_defaults(self, ui_state):
        assert ui_state.current_menu_id == "main"
        assert ui_state.history == []
        assert ui_state.modal is None


class TestUIStateNavigation:
    def test_push_menu(self, ui_state):
        ui_state.push_menu("settings")
        assert ui_state.current_menu_id == "settings"
        assert ui_state.history == ["main"]

    def test_push_multiple(self, ui_state):
        ui_state.push_menu("settings")
        ui_state.push_menu("security")
        assert ui_state.current_menu_id == "security"
        assert ui_state.history == ["main", "settings"]

    def test_pop_menu(self, ui_state):
        ui_state.push_menu("settings")
        ui_state.pop_menu()
        assert ui_state.current_menu_id == "main"
        assert ui_state.history == []

    def test_pop_empty_returns_main(self, ui_state):
        ui_state.current_menu_id = "orphan"
        ui_state.pop_menu()
        assert ui_state.current_menu_id == "main"

    def test_clear_history(self, ui_state):
        ui_state.push_menu("a")
        ui_state.push_menu("b")
        ui_state.clear_history()
        assert ui_state.history == []
        assert ui_state.current_menu_id == "b"


class TestUIStateModals:
    def test_open_modal(self, ui_state):
        ui_state.open_modal("confirm")
        assert ui_state.modal == "confirm"
        assert ui_state.is_modal_open() is True

    def test_close_modal(self, ui_state):
        ui_state.open_modal("confirm")
        ui_state.close_modal()
        assert ui_state.modal is None
        assert ui_state.is_modal_open() is False

    def test_is_modal_open_default(self, ui_state):
        assert ui_state.is_modal_open() is False
