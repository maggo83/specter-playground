"""Seed placeholder used by the MockUI state.

Represents a loaded MasterKey (seedphrase) in memory.
Ephemeral — never persisted across power cycles in working memory.
"""
import urandom

class Seed:
    """Tiny seed placeholder used by SpecterState.

    Attributes:
        label: user-given display name (e.g., "My Key")
        fingerprint: master fingerprint hex string (e.g., "a1b2c3d4")
        passphrase: optional BIP-39 passphrase (None if not set)
        passphrase_active: True if passphrase is currently applied
        is_backed_up: True when seed was loaded from storage (QR/SD/SmartCard/
                      flash/keyboard) or user explicitly confirmed it is backed up.
                      False for freshly generated seeds not yet confirmed.
    """

    def __init__(self, label, fingerprint=None, passphrase=None,
                 passphrase_active=False, is_backed_up=False):
        self.label = label
        self.fingerprint = fingerprint or self.generate_dummy_fingerprint()
        self.passphrase = passphrase
        self.passphrase_active = passphrase_active
        self.is_backed_up = is_backed_up

    @staticmethod
    def generate_dummy_fingerprint():
        """Generate a fake fingerprint for mock purposes."""
        h = hex(urandom.getrandbits(16))[:]
        return h
    
    def get_fingerprint(self):
        """Return the fingerprint of this seed."""
        if self.passphrase is not None and self.passphrase_active:
            # In a real implementation, the fingerprint would change if a passphrase is active.
            # For this mock, we'll just reverse the hex digits (keeping any 0x prefix).
            # Note: MicroPython does not support step=-1 slices, so use reversed().
            fp = self.fingerprint
            if fp.startswith("0x") or fp.startswith("0X"):
                return fp[:2] + "".join(reversed(fp[2:]))
            return "".join(reversed(fp))
        else:   
            return self.fingerprint

    @staticmethod
    def get_fingerprints(seeds):
        """Return list of fingerprints for a list of seeds."""
        return [seed.fingerprint for seed in seeds]