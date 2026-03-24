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
    """

    def __init__(self, label, fingerprint=None, passphrase=None):
        self.label = label
        self.fingerprint = fingerprint or self.generate_dummy_fingerprint()
        self.passphrase = passphrase

    @staticmethod
    def generate_dummy_fingerprint():
        """Generate a fake fingerprint for mock purposes."""
        h = hex(urandom.getrandbits(16))[:]
        return h
    
    @staticmethod
    def get_fingerprints(seeds):
        """Return list of fingerprints for a list of seeds."""
        return [seed.fingerprint for seed in seeds]