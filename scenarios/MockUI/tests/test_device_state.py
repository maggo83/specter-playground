"""Tests for SpecterState."""
from MockUI.helpers.device_state import SpecterState
from MockUI.helpers.wallet import Wallet


class TestSpecterStateInit:
    def test_defaults(self, specter_state):
        assert specter_state.seed_loaded is False
        assert specter_state.active_wallet is None
        assert specter_state.registered_wallets == []
        assert specter_state.is_locked is False
        assert specter_state.pin is None


class TestSpecterStateWallets:
    def test_register_wallet(self, specter_state, wallet):
        specter_state.register_wallet(wallet)
        assert len(specter_state.registered_wallets) == 1
        assert specter_state.registered_wallets[0] is wallet

    def test_register_multiple(self, specter_state):
        w1 = Wallet("W1")
        w2 = Wallet("W2")
        specter_state.register_wallet(w1)
        specter_state.register_wallet(w2)
        assert len(specter_state.registered_wallets) == 2

    def test_set_active_wallet(self, specter_state, wallet):
        specter_state.set_active_wallet(wallet)
        assert specter_state.active_wallet is wallet

    def test_clear_wallets(self, specter_state, wallet):
        specter_state.register_wallet(wallet)
        specter_state.clear_wallets()
        assert specter_state.registered_wallets == []


class TestSpecterStateLocking:
    def test_lock(self, specter_state):
        specter_state.lock()
        assert specter_state.is_locked is True

    def test_unlock_no_pin(self, specter_state):
        specter_state.lock()
        result = specter_state.unlock()
        assert result is True
        assert specter_state.is_locked is False

    def test_unlock_correct_pin(self, specter_state):
        specter_state.pin = "1234"
        specter_state.lock()
        result = specter_state.unlock("1234")
        assert result is True
        assert specter_state.is_locked is False

    def test_unlock_wrong_pin(self, specter_state):
        specter_state.pin = "1234"
        specter_state.lock()
        result = specter_state.unlock("0000")
        assert result is False
        assert specter_state.is_locked is True


class TestSpecterStatePeripherals:
    def test_peripheral_defaults(self, specter_state):
        assert specter_state.hasUSB is True
        assert specter_state.enabledUSB is False
        assert specter_state.hasQR is False
        assert specter_state.hasSD is False
