"""Simple in-memory state holder for the mock UI.

Lightweight and runtime-friendly: avoids typing imports and annotations so
it works cleanly in the MicroPython host/simulator environment.
"""


from .wallet import Wallet
from .seed import Seed


class SpecterState:
    """Mutable application state used by the mock UI.

    All attributes are intentionally public and mutable for simplicity.
    """

    def __init__(self):

       # device features
        self.has_battery = False
        self.battery_pct = None
        self.is_charging = False
        
        self.is_locked = False
        self.pin = None

        # Seed related — ephemeral, cleared on power cycle
        self.loaded_seeds = []
        self.active_seed = None

        # Wallet (descriptor) related — persisted in flash
        self.active_wallet = None
        self.registered_wallets = []

        #KeyStores
        self._SmartCard_hasSeed = False
        self._SD_hasSeed = False
        self._Flash_hasSeed = False

        # peripherals        
        self._hasQR = False
        self._enabledQR = False

        self._hasSD = False
        self._enabledSD = False
        self._detectedSD = False

        self._hasUSB = True
        self._enabledUSB = False

        self._hasSmartCard = False
        self._enabledSmartCard = False
        self._detectedSmartCard = False

        # misc
        self.language = "eng"
        self.fw_version = "1.0"

    
    # ── Interface for UI state queries ───────────────────────────────
    def hasSmartCard(self):
        return self._hasSmartCard
    def SmartCard_enabled(self):
        return self.hasSmartCard() and self._enabledSmartCard
    def SmartCard_detected(self):
        return self.SmartCard_enabled() and self._detectedSmartCard
    def SmartCard_hasSeed(self):
        return self.SmartCard_detected() and self._SmartCard_hasSeed
    def hasSD(self):
        return self._hasSD
    def SD_enabled(self):
        return self.hasSD() and self._enabledSD
    def SD_detected(self):
        return self.SD_enabled() and self._detectedSD
    def SD_hasSeed(self):
        return self.SD_detected() and self._SD_hasSeed
    def hasQR(self):
        return self._hasQR
    def QR_enabled(self):
        return self.hasQR() and self._enabledQR
    def Flash_hasSeed(self):
        return self._Flash_hasSeed
    def hasUSB(self):
        return self._hasUSB
    def USB_enabled(self):
        return self.hasUSB() and self._enabledUSB

    # ── Seed helpers ─────────────────────────────────────────────────
    def add_seed(self, seed):
        """Load a seed into memory and make it active."""
        self.loaded_seeds.append(seed)
        # Auto-create default wallet for this seed if none exists
        default_wallet = self._ensure_default_wallet()
        if not self.active_wallet:
            self.set_active_wallet(default_wallet)
        self.set_active_seed(seed)

    def set_active_seed(self, seed):
        """Switch the active seed. Auto-adjusts active wallet if needed."""
        self.active_seed = seed

        # If current wallet doesn't match the new seed, switch to default
        if not self.seed_matches_wallet(seed, self.active_wallet):
            self.active_wallet = self._ensure_default_wallet()

    def remove_seed(self, seed):
        """Remove a seed from loaded seeds and clean up all wallets it owns."""
        if seed in self.loaded_seeds:
            self.loaded_seeds.remove(seed)
        if self.active_seed is seed:
            self.active_seed = self.loaded_seeds[0] if self.loaded_seeds else None
        # Remove wallets that belonged exclusively to this seed (non-default, not multisig shared)
        fp = seed.get_fingerprint()
        self.registered_wallets = [
            w for w in self.registered_wallets
            if not (fp in w.required_fingerprints and len(w.required_fingerprints) == 1 and not w.is_default_wallet())
        ]
        if self.active_wallet not in self.registered_wallets:
            self.active_wallet = self.registered_wallets[0] if self.registered_wallets else None

    def wallets_for_seed(self, seed):
        """Return wallets that match this seed (including the shared Default Wallet)."""
        if seed is None:
            return None
        fp = seed.get_fingerprint()
        return [wallet for wallet in self.registered_wallets
                if wallet.is_default_wallet() or fp in wallet.required_fingerprints]

    def seed_matches_wallet(self, seed=None, wallet=None):
        """Check if a seed's fingerprint is in the wallet's required signers."""
        if not seed:
            seed=self.active_seed
        if not wallet:
            wallet=self.active_wallet
        if not seed or not wallet:
            return False
        return wallet in self.wallets_for_seed(seed)

    # ── Wallet helpers ───────────────────────────────────────────────
    def register_wallet(self, wallet, imported=False):
        """Register a wallet descriptor.

        Args:
            wallet: Wallet instance to register.
            imported: If True, mark has_been_exported=True because the
                wallet was received from a companion app (QR scan / SD card)
                and therefore already "connected".
        """
        if imported:
            wallet.has_been_exported = True
        self.registered_wallets.append(wallet)
        self.set_active_wallet(wallet)

    def set_active_wallet(self, wallet):
        self.active_wallet = wallet

    def remove_wallet(self, wallet):
        """Remove a wallet and select the next available one."""
        if wallet in self.registered_wallets:
            self.registered_wallets.remove(wallet)
        if self.active_wallet is wallet:
            candidate_wallets = None
            if self.active_seed is not None:
                candidate_wallets = self.wallets_for_seed(self.active_seed)
            else:
                candidate_wallets = self.registered_wallets
            self.active_wallet = candidate_wallets[0] if candidate_wallets else None

    def _ensure_default_wallet(self):
        """Ensure the shared Default Wallet exists.
        There is only ONE Default Wallet that fits any loaded key."""
        for wallet in self.registered_wallets:
            if wallet.is_default_wallet():
                return wallet
        # Create the singleton Default Wallet
        wallet = Wallet(
            label="Default",
            descriptor="default",
            isMultiSig=False,
            net="mainnet",
            required_fingerprints=[],
        )
        self.registered_wallets.append(wallet)
        return wallet

    def seeds_for_wallet(self, wallet):
        """Return seeds that match this wallet (including the shared Default Wallet)."""
        if wallet is None:
            return None
        if wallet.is_default_wallet():
            # Default wallet matches any seed
            return self.loaded_seeds
        
        fps = set(wallet.required_fingerprints)
        return [seed for seed in self.loaded_seeds
                if seed.get_fingerprint() in fps] 

    def signing_match_count(self, wallet = None):
        """Return (matched_count, required_count) for the given wallet (default: active wallet)."""
        if not wallet:
            wallet = self.active_wallet

        if not wallet:
            return (0, 0)
        # Default wallet: always 1-of-1 when a seed is loaded
        if wallet.is_default_wallet():
            return (1, 1) if self.active_seed else (0, 1)
        
        if wallet.is_standard():
            loaded_fps = set(seed.get_fingerprint() for seed in self.loaded_seeds)
            matched = len(loaded_fps & set(wallet.required_fingerprints))
            return (matched, len(wallet.required_fingerprints))
        else:
            # For non-standard wallets, we can't analyze the descriptor, so just return dummy values
            return (1, 1) if self.active_seed else (0, 1)

    # ── Lock helpers ─────────────────────────────────────────────────
    def lock(self):
        self.is_locked = True

    def unlock(self, pin=None):
        # naive PIN check for mock; in real code use secure compare
        if self.pin is None or pin == self.pin:
            self.is_locked = False
            return True
        return False
