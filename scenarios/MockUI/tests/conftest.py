"""Pytest configuration for MockUI state tests."""
import pytest

# Import state classes (micropython/lvgl already mocked by scenarios/conftest.py)
from MockUI.helpers.device_state import SpecterState
from MockUI.helpers.ui_state import UIState
from MockUI.helpers.wallet import Wallet


@pytest.fixture
def specter_state():
    """Fresh SpecterState instance."""
    return SpecterState()


@pytest.fixture
def ui_state():
    """Fresh UIState instance."""
    return UIState()


@pytest.fixture
def wallet():
    """Sample wallet."""
    return Wallet("Test Wallet", xpub="xpub123")


@pytest.fixture
def multisig_wallet():
    """Sample multisig wallet."""
    return Wallet("Multisig", isMultiSig=True, net="testnet")
