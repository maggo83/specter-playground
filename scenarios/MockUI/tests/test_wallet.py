"""Tests for Wallet model."""
from MockUI.helpers.wallet import Wallet


class TestWallet:
    def test_init_defaults(self):
        w = Wallet("MyWallet")
        assert w.name == "MyWallet"
        assert w.xpub is None
        assert w.isMultiSig is False
        assert w.net == "mainnet"
        assert w.active_passphrase is None

    def test_init_full(self):
        w = Wallet("Test", xpub="xpub123", isMultiSig=True, net="testnet")
        assert w.name == "Test"
        assert w.xpub == "xpub123"
        assert w.isMultiSig is True
        assert w.net == "testnet"

    def test_passphrase_assignment(self, wallet):
        wallet.active_passphrase = "secret"
        assert wallet.active_passphrase == "secret"
