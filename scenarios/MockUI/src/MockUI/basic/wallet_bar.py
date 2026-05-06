import lvgl as lv
from .ui_consts import BTC_ICON_WIDTH, GREEN_HEX, WHITE_HEX, SCREEN_WIDTH
from .widgets.icon_widgets import make_icon
from .symbol_lib import BTC_ICONS, Icon
from ..stubs import Wallet


class WalletBar(lv.obj):
    """Wallet status bar showing Seed and Wallet info.

    Flat flex row layout (no sub-containers, no overlap):
        seed name (right-aligned) | @fingerprint | passphrase icon | ~~spacer~~ | key icon | custom icon | wallet name | network
    Seed name is right-aligned so short names sit flush against fingerprint.
    Wallet name is left-aligned so short names sit flush against key icon/custom icon.
    When custom icon is hidden (standard wallet), wallet name expands to fill
    the freed slot, keeping the network label in a fixed position.
    """

    # ── Fixed slot widths (pixels) ──────────────────────────────────────────
    # Screen is 480px wide (portrait). Margins 15px each side → 450px usable.
    # Split in half for left: Seed and right: Wallet → 225px each side.

    WALLET_BAR_VERTICAL_MARGIN = 15  # vertical border between wallet bar items and the left/rigth screenborder (px)
    LETTER_W     = 12    # for truncating text to fit in fixed-width slots (approximate, depends on chars)
    # Left side
    SEED_NAME_W   = 90    # ~9 chars at font_16
    PP_ICON_W     = BTC_ICON_WIDTH   # 42 (passphrase indicator, usually hidden)
    FINGERPRINT_ICON_W = BTC_ICON_WIDTH   # 42 (using key icon as fingerprint indicator, for simplicity and icon consistency) --- IGNORE ---
    FINGERPRINT_W = 40    # ~4 chars
    # Right side
    WALLET_NAME_W = 90    # ~9 chars
    KEY_ICON_W    = BTC_ICON_WIDTH   # 42
    CUSTOM_ICON_W = BTC_ICON_WIDTH   # 42 (non-standard indicator, usually hidden)
    NET_W         = 40    # ~4 chars : "main"/"test"/"sig" 

    def __init__(self, gui, height_pct=5):
        super().__init__(gui)

        self.gui = gui
        self.state = gui.specter_state
        self.t = gui.i18n.t

        self.set_width(lv.pct(100))
        self.set_height(lv.pct(height_pct))

        self.set_layout(lv.LAYOUT.FLEX)
        self.set_flex_flow(lv.FLEX_FLOW.ROW)
        self.set_flex_align(
            lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER
        )
        self.set_style_pad_left(self.WALLET_BAR_VERTICAL_MARGIN, 0)
        self.set_style_pad_right(self.WALLET_BAR_VERTICAL_MARGIN, 0)
        self.set_style_pad_top(0, 0)
        self.set_style_pad_bottom(0, 0)
        self.set_style_pad_column(0, 0)
        self.set_style_radius(0, 0)
        self.set_style_border_width(0, 0)

        self.font = lv.font_montserrat_16

        # ── Left/Right containers ────────────────────────────────────────────
        # LEFT: Seed
        self.left_container = WalletBar._create_container(
            self,
            SCREEN_WIDTH // 2 - self.WALLET_BAR_VERTICAL_MARGIN,
            alignment=lv.FLEX_ALIGN.END
        )
        self.left_container.set_style_pad_right(5, 0)

        # RIGHT: Wallet
        self.right_container = WalletBar._create_container(
            self,
            SCREEN_WIDTH // 2 - self.WALLET_BAR_VERTICAL_MARGIN,
            alignment=lv.FLEX_ALIGN.END
        )

        # ── Elements in containers ────────────────────────────────────────────
        # ── Left elements (Seed) ──────────────────────────────────────────────
        self.seed_name_lbl = WalletBar._create_bar_item(
            self.left_container, 
            "", 
            width=self.SEED_NAME_W,
            font=self.font,
            click_cb=self._goto_addchose_seed
        )
        self.seed_name_lbl.set_style_text_align(lv.TEXT_ALIGN.RIGHT, 0)

        self.passphrase_img = WalletBar._create_bar_item(
            self.left_container,
            BTC_ICONS.PASSWORD,
            width=self.PP_ICON_W,
            font=None,
            click_cb=self._goto_manage_seedphrase
        )
        self.fingerprint_img = WalletBar._create_bar_item(
            self.left_container,
            BTC_ICONS.RELAY,
            width=self.FINGERPRINT_ICON_W,
            font=None,
            click_cb=self._goto_manage_seedphrase
        )
        self.fingerprint_lbl = WalletBar._create_bar_item(
            self.left_container,
            "",
            width=self.FINGERPRINT_W,
            font=self.font,
            click_cb=self._goto_manage_seedphrase
        )
        self.fingerprint_lbl.set_style_text_align(lv.TEXT_ALIGN.LEFT, 0)

        # ── Right elements (Wallet) ─────────────────────────────────────────
        self.wallet_name_lbl = WalletBar._create_bar_item(
            self.right_container,
            "",
            width=self.WALLET_NAME_W,
            font=self.font,
            click_cb=self._goto_addchose_wallet
        )
        self.wallet_name_lbl.set_style_text_align(lv.TEXT_ALIGN.RIGHT, 0)

        self.custom_img = WalletBar._create_bar_item(   
            self.right_container,
            BTC_ICONS.CONSOLE,
            width=self.CUSTOM_ICON_W,
            font=None,
            click_cb=self._goto_manage_wallet
        )

        self.key1_img = WalletBar._create_bar_item(
            self.right_container,
            BTC_ICONS.KEY,  # default icon, updated to reflect signing status in refresh()
            width=self.KEY_ICON_W,
            font=None,
            click_cb=self._goto_manage_wallet
        )

        self.net_lbl = WalletBar._create_bar_item(
            self.right_container,
            "",
            width=self.NET_W,
            font=self.font,
            click_cb=self._goto_manage_wallet
        )
        self.net_lbl.set_style_text_align(lv.TEXT_ALIGN.RIGHT, 0)

    # ── Construction helpers─────────────────────────────────────────────────
    @staticmethod
    def _create_container(parent, width, alignment=lv.FLEX_ALIGN.CENTER):
        """Helper to create a left-, center- or right-aligned container with given width."""
        cont = lv.obj(parent)
        cont.set_width(width)
        cont.set_height(lv.pct(100))
        cont.set_layout(lv.LAYOUT.FLEX)
        cont.set_flex_flow(lv.FLEX_FLOW.ROW)
        cont.set_flex_align(alignment, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
        cont.set_style_pad_all(0, 0)
        cont.set_style_border_width(0, 0)
        return cont
    
    @staticmethod
    def _create_bar_item(parent, item_data = "", width=10, font=lv.font_montserrat_16, click_cb=None):
        """Helper to create a bar item with given text, width and click callback."""

        #Determine item type based on input data. Default: string
        item_type = "str"
        if item_data is None:
            item_data = ""
        elif isinstance(item_data, Icon):
            item_type = "icon"

        if item_type == "str":
            lbl = lv.label(parent)
            lbl.set_long_mode(lv.label.LONG_MODE.CLIP)
            lbl.set_text(item_data)
            lbl.set_width(width)
            lbl.set_style_text_font(font, 0)
            if click_cb:
                lbl.add_flag(lv.obj.FLAG.CLICKABLE)
                lbl.add_event_cb(click_cb, lv.EVENT.CLICKED, None)
            return lbl
        elif item_type == "icon":
            img = make_icon(parent, item_data, width=width)
            if click_cb:
                img.add_flag(lv.obj.FLAG.CLICKABLE)
                img.add_event_cb(click_cb, lv.EVENT.CLICKED, None)
            return img

    # ── Click callbacks ─────────────────────────────────────────────────────

    def _goto_addchose_seed(self, e):
        """Switch / Add MasterKey (or Add if none)."""
        if e.get_code() != lv.EVENT.CLICKED:
            return
        cur_menu = self.gui.ui_state.current_menu_id
        if self.state.active_seed is None:
            if cur_menu != "add_seed":
                self.gui.show_menu("add_seed")
        else:
            if cur_menu != "switch_add_seeds":
                self.gui.show_menu("switch_add_seeds")

    def _goto_manage_seedphrase(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return
        cur_menu = self.gui.ui_state.current_menu_id
        if self.state.active_seed and cur_menu != "manage_seedphrase":
            self.gui.show_menu("manage_seedphrase")

    def _goto_addchose_wallet(self, e):
        """Switch / Add Wallet."""
        if e.get_code() != lv.EVENT.CLICKED:
            return
        cur_menu = self.gui.ui_state.current_menu_id
        if self.state.active_wallet and cur_menu != "switch_add_wallets":
            self.gui.show_menu("switch_add_wallets")

    def _goto_manage_wallet(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return
        cur_menu = self.gui.ui_state.current_menu_id
        if self.state.active_wallet and cur_menu != "manage_wallet":
            self.gui.show_menu("manage_wallet")

    # ── Refresh ─────────────────────────────────────────────────────────────

    def refresh(self, state):
        """Update all visual elements from state."""
        if state.is_locked:
            self._clear_all()
            return

        # ── Left side: MasterKey ────────────────────────────────────────────
        seed = state.active_seed
        if not seed:
            self.seed_name_lbl.set_text(self.t("WALLET_BAR_NO_SEED"))
            self._hide_img(self.fingerprint_img)
            self.fingerprint_lbl.set_text("")
            self._hide_img(self.passphrase_img)
        else:
            #if no pasphrase is applied, use the extra space to show more of the seed name
            seed_name_w = self.SEED_NAME_W

            if not seed.passphrase:
                self._hide_img(self.passphrase_img)
                seed_name_w += self.PP_ICON_W
            else:
                self._show_img(self.passphrase_img)

            self.seed_name_lbl.set_width(seed_name_w)
            self.seed_name_lbl.set_text(seed.label[:(seed_name_w // self.LETTER_W)])

            self._show_img(self.fingerprint_img)
            #do not show "0x" hex prefix in fingerprint
            self.fingerprint_lbl.set_text(seed.fingerprint[2:])
    

        # ── Right side: Wallet (conditional) ────────────────────────────────
        show_wallet_side = self._should_show_wallet_side(state)

        if not show_wallet_side:
            self._clear_wallet_side()
            return
        
        # Divider to Seed section: 1px border on right side of left container
        self.left_container.set_style_border_width(2, 0)
        self.left_container.set_style_border_color(WHITE_HEX, 0)
        self.left_container.set_style_border_side(lv.BORDER_SIDE.RIGHT, 0)


        wallet = state.active_wallet
        if not wallet:
            # Show "Default" only when multiple keys loaded but no wallet; otherwise hide entire wallet side, see above
            self.wallet_name_lbl.set_text(self.t("WALLET_BAR_NO_WALLET"))
            self._hide_img(self.custom_img)
            self._show_img(self.key1_img, BTC_ICONS.KEY(GREEN_HEX))
            self.net_lbl.set_text(self._get_net_text("mainnet"))
        else:
            # Wallet name and standardness icon
            #if wallet is standard, use the extra space to show more of the wallet name
            wallet_name_w = self.WALLET_NAME_W
            if wallet.is_standard():
                self._hide_img(self.custom_img)
                wallet_name_w += self.CUSTOM_ICON_W
            else:
                self._show_img(self.custom_img)

            self.wallet_name_lbl.set_width(wallet_name_w)
            self.wallet_name_lbl.set_text(wallet.label[:(wallet_name_w // self.LETTER_W)])

            # Key icon with signing-readiness color coding
            matched, total = state.signing_match_count()
            if wallet.isMultiSig:
                # Two-keys icon; green when threshold met, and matches active seed, white otherwise
                threshold_met = wallet.threshold and matched >= wallet.threshold
                seed_wallet_match = self.state.seed_matches_wallet()
                color = GREEN_HEX if threshold_met and seed_wallet_match else WHITE_HEX
                self._show_img(self.key1_img, BTC_ICONS.TWO_KEYS(color))
            else:
                # Single KEY icon
                color = GREEN_HEX if matched >= 1 else WHITE_HEX
                self._show_img(self.key1_img, BTC_ICONS.KEY(color))

            # Network
            net_text = self._get_net_text(wallet.net)
            self.net_lbl.set_text(net_text[:4])



    def _should_show_wallet_side(self, state):
        """Determine if the wallet side of the bar should be visible."""
        if state.active_wallet is None:
            return False
        # Suppress wallet side for single key + default wallet only
        if (len(state.loaded_seeds) <= 1
                and len(state.registered_wallets) <= 1
                and not state.active_wallet.isMultiSig
                and state.active_wallet.is_default_wallet()):
            return False
        return True

    def _clear_all(self):
        """Clear all elements (e.g. in locked state)."""
        self._clear_seed_side()
        self._clear_wallet_side()

    def _clear_seed_side(self):
        """Clear all seed-side elements."""
        self.seed_name_lbl.set_text("")
        self._hide_img(self.passphrase_img)
        self._hide_img(self.fingerprint_img)
        self.fingerprint_lbl.set_text("")

    def _clear_wallet_side(self):
        """Clear all wallet-side elements."""
        self.wallet_name_lbl.set_text("")
        self._hide_img(self.custom_img)
        self._hide_img(self.key1_img)
        self.net_lbl.set_text("")

        # Divider to Seed section: set to 0px border on right side of left container
        self.left_container.set_style_border_width(0, 0)
        self.left_container.set_style_border_color(WHITE_HEX, 0)
        self.left_container.set_style_border_side(lv.BORDER_SIDE.RIGHT, 0)        

    def _hide_img(self, img):
        """Clear image source and hide so it takes no flex space."""
        img.add_flag(lv.obj.FLAG.HIDDEN)
        img.set_width(0)

    def _show_img(self, img, icon=None):
        """Unhide image, and if new image is passed: set it."""
        img.set_width(BTC_ICON_WIDTH)
        img.remove_flag(lv.obj.FLAG.HIDDEN)
        if icon is not None:
            icon.add_to_parent(img)

    def _get_net_text(self, net):
        """Return display text for network."""
        net_map = {"mainnet": "main", "testnet": "test", "signet": "sig"}
        return net_map.get(net, net or "")
