PROFILE_WALLET_NAME = "wallet_name"
PROFILE_PASSPHRASE_GENERAL = "passphrase_general"
PROFILE_SEED_NAME = "seed_name"


_WALLET_ACCEPTED = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?/~ "
_PASSPHRASE_ACCEPTED = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?/~ "


PROFILE_CONFIG = {
    PROFILE_WALLET_NAME: {
        "accepted_chars": _WALLET_ACCEPTED,
        "trim_edges": True,
    },
    PROFILE_PASSPHRASE_GENERAL: {
        "accepted_chars": _PASSPHRASE_ACCEPTED,
        "trim_edges": True,
    },
    PROFILE_SEED_NAME: {
        "accepted_chars": _WALLET_ACCEPTED,
        "trim_edges": True,
    },
}


def get_profile_config(profile_id):
    return PROFILE_CONFIG[profile_id]


def accepted_chars(profile_id):
    return PROFILE_CONFIG[profile_id]["accepted_chars"]


def sanitize_text(profile_id, text):
    cfg = PROFILE_CONFIG[profile_id]
    if cfg.get("trim_edges"):
        return text.strip()
    return text
