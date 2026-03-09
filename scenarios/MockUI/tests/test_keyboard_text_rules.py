from MockUI.basic.keyboard_text_rules import (
    PROFILE_PASSPHRASE_GENERAL,
    PROFILE_WALLET_NAME,
    sanitize_text,
)


def test_passphrase_trims_leading_and_trailing_spaces():
    assert sanitize_text(PROFILE_PASSPHRASE_GENERAL, "  my passphrase  ") == "my passphrase"


def test_passphrase_keeps_internal_spaces():
    assert sanitize_text(PROFILE_PASSPHRASE_GENERAL, "alpha   beta") == "alpha   beta"


def test_wallet_name_trims_leading_and_trailing_spaces():
    assert sanitize_text(PROFILE_WALLET_NAME, "  My Wallet  ") == "My Wallet"
