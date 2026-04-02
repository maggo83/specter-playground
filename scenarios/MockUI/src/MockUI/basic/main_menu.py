from .menu import GenericMenu
import lvgl as lv
from .symbol_lib import BTC_ICONS
from .ui_consts import GREEN_HEX, RED_HEX, WHITE_HEX


class MainMenu(GenericMenu):
    TITLE_KEY = "MAIN_MENU_TITLE"

    def get_menu_items(self, t, state):
        has_seed = state and state.active_seed is not None

        if not has_seed:
            return self._items_no_seed(t, state)
        else:
            return self._items_with_seed(t, state)
        
    def post_init(self, t, state):
        #Add Seed and Wallet lable to title when loaded
        has_seed = state and state.active_seed is not None    

        if has_seed:
            menu_title = self.title.get_text()
            seed_wallet_title = state.active_seed.label

            if not state.active_wallet.is_default_wallet():
                seed_wallet_title += " - " + state.active_wallet.label

            self.title.set_text(seed_wallet_title)
        

    def _items_no_seed(self, t, state):
        """State: No Seed loaded yet — focus on key loading."""
        menu_items = []
        slots_available = 6.5
        slots_used = 2 + int(state.SmartCard_hasSeed()) + int(state.SD_hasSeed()) + int(state.Flash_hasSeed() + int(state.QR_enabled()))
        slots_remaining = slots_available - slots_used

        Seed_detected = (state.SmartCard_hasSeed() or state.SD_hasSeed() or state.Flash_hasSeed())

        menu_items.append((None, t("ADD_SEED_GENERATE_SECTION"), None, None, None, None))

        # Generate New Key
        gen_size = 1.0+slots_remaining/slots_used if not Seed_detected else 1
        menu_items.append((BTC_ICONS.MNEMONIC, t("ADD_SEED_GENERATE_SEED"), "generate_seedphrase", None, gen_size, None))

        menu_items.append((None, t("ADD_SEED_IMPORT_SECTION"), None, None, None, None))

        # SmartCard (highlighted exclusively when detected with key)
        if state.SmartCard_hasSeed():
            sc_size = 1.0 + slots_remaining
            menu_items.append((BTC_ICONS.SMARTCARD, t("HARDWARE_SMARTCARD"), "import_from_smartcard", None, sc_size, None))

        # Scan QR
        qr_size = 1.0+slots_remaining/slots_used if not Seed_detected else 1
        if state.QR_enabled():
            menu_items.append((BTC_ICONS.SCAN, t("HARDWARE_QR_CODE"), "import_from_qr", None, qr_size, None))

        # Keyboard
        kb_size = 1.0+slots_remaining/slots_used if not Seed_detected else 1
        menu_items.append((lv.SYMBOL.KEYBOARD, t("COMMON_KEYBOARD"), "import_from_keyboard", None, kb_size, None))

        # SD Card (only if key data detected)
        if state.SD_hasSeed():
            sd_size = 1.0 + slots_remaining if not state.SmartCard_hasSeed() else 1
            menu_items.append((BTC_ICONS.SD_CARD, t("HARDWARE_SD_CARD"), "import_from_sd", None, sd_size, None))

        # Flash (only if key data in flash)
        if state.Flash_hasSeed():
            flash_size = 1.0 + slots_remaining if not (state.SmartCard_hasSeed() or state.SD_hasSeed()) else 1
            menu_items.append((BTC_ICONS.FILE, t("HARDWARE_INTERNAL_FLASH"), "import_from_flash", None, flash_size, None))

        return menu_items

    def _items_with_seed(self, t, state):
        """State: Seed loaded — normal operating mode."""
        menu_items = []

        has_controlled_input = (state.QR_enabled() or state.SD_detected())
        can_sign_msg = (state.active_wallet
                        and not state.active_wallet.isMultiSig
                        and state.seed_matches_wallet()
                        and has_controlled_input)
        
        active_wallet_was_never_exported = state.active_wallet and not state.active_wallet.has_been_exported

        # ── Actions section ─────────────────────────────────────────────────

        if has_controlled_input or can_sign_msg:
            menu_items.append((None, t("MAIN_MENU_PROCESS_INPUT"), None, None, None, None))
            if state.QR_enabled():
                menu_items.append((BTC_ICONS.SCAN, t("MAIN_MENU_SCAN_QR"), "scan_qr", None, 1.3, "HELP_SCAN_QR"))
            if state.SD_detected():
                menu_items.append((BTC_ICONS.SD_CARD, t("MAIN_MENU_LOAD_FROM_SD"), "load_sd", None, 1, None))
            if can_sign_msg:
                menu_items.append((BTC_ICONS.SIGN, t("MAIN_MENU_SIGN_MESSAGE"), "sign_message", None, 1, None))

        # ── Seed & Wallet section ───────────────────────────────────────────
        menu_items.append((None, t("MAIN_MENU_SEED_AND_WALLET"), None, None, None, None))
        menu_items.append((BTC_ICONS.MNEMONIC, t("MAIN_MENU_MANAGE_SEED_WALLET"), "manage_seed_wallet", None, 1, None))

        # ── Connect Companion App (only if wallet not yet exported) ─────────
        if active_wallet_was_never_exported:
            menu_items.append((None, t("MAIN_MENU_CONNECT_SECTION"), None, None, None, None))
            menu_items.append((BTC_ICONS.LINK, t("MAIN_MENU_CONNECT_COMPANION"), "connect_sw_wallet", None, 1.5, None))

        return menu_items
