"""Seed placeholder used by the MockUI state.

Represents a loaded MasterKey (seedphrase) in memory.
Ephemeral — never persisted across power cycles in working memory.
"""


class Seed:
    """Tiny seed placeholder used by SpecterState.

    Attributes:
        label: user-given display name (e.g., "My Key")
        fingerprint: master fingerprint hex string (e.g., "a1b2c3d4")
        passphrase: optional BIP-39 passphrase (None if not set)
    """

    def __init__(self, label, fingerprint=None, passphrase=None):
        self.label = label
        self.fingerprint = fingerprint or self._generate_dummy_fingerprint()
        self.passphrase = passphrase

    def _generate_dummy_fingerprint(self):
        """Generate a fake fingerprint for mock purposes."""
        try:
            import urandom
            h = hex(urandom.getrandbits(32))[2:]
            return "0" * (8 - len(h)) + h
        except ImportError:
            import random
            h = hex(random.getrandbits(32))[2:]
            return "0" * (8 - len(h)) + h
