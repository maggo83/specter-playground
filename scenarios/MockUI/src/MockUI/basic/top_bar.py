"""TopBar — permanent top status bar for Specter MockUI.

Replaces DeviceBar. Shows battery + context-dependent seed/wallet info.

Layout (left-to-right, full width, STATUS_BAR_PCT% height):
    ┌──────────────────────────────────────────────────────────────────┐
    │ [seed name] [relay][fp4] [pp?] [warn?] [/] [wallet] [type] ...  🔋│
    └──────────────────────────────────────────────────────────────────┘

Battery is always at the rightmost edge (STATUS_BTN_WIDTH wide slot).

Visibility rules
────────────────
- Locked                          → battery only
- No seeds loaded / >1 seeds      → battery only
- Exactly 1 seed loaded           → seed section + optional wallet section
- Wallet section shows only when exactly 1 non-default wallet is loaded

Seed section (left-to-right):
  1. Seed name     — dynamic font (font_28 → 22 → 16, optional two-line)
  2. Fingerprint   — RELAY icon + first 4 hex chars (no "0x" prefix)
  3. Passphrase?   — PASSWORD icon (white=active, grey=inactive), only when
                     passphrase is set; clickable to toggle passphrase_active
  4. Backup warn?  — ALERT_CIRCLE (orange), only when seed.is_backed_up==False

Wallet section (only when exactly 1 non-default wallet):
  5. Separator     — "/" text
  6. Wallet name   — dynamic font
  7. Type icon     — KEY (singlesig) / TWO_KEYS (multisig) / CONSOLE (custom);
                     white when all required keys loaded, grey otherwise
  8. Account?      — "#N" if wallet.account != 0
  9. Network?      — "test"/"sig" if not mainnet
"""

import lvgl as lv
from ..stubs import Battery
from .ui_consts import (
    BTC_ICON_WIDTH, STATUS_BTN_HEIGHT, STATUS_BTN_WIDTH,
    GREEN_HEX, WHITE_HEX, GREY_HEX, ORANGE_HEX, SCREEN_WIDTH,
)
from .symbol_lib import BTC_ICONS
from .widgets.containers import flex_row
from .widgets.action_modal import ActionModal

# ── Name-label font helpers (ported from TopSelector) ────────────────────────
_NAME_FONTS = [
    lv.font_montserrat_28,
    lv.font_montserrat_22,
    lv.font_montserrat_16,
]

# Fixed-width slots (px) used for budget calculation
_FP_ICON_W  = BTC_ICON_WIDTH          # RELAY icon
_FP_TEXT_W  = 40                       # 4-char hex fingerprint
_PP_ICON_W  = BTC_ICON_WIDTH           # PASSWORD icon (optional)
_WARN_ICON_W = BTC_ICON_WIDTH          # ALERT_CIRCLE icon (optional)
_SEP_W       = 20                      # "/" separator
_TYPE_ICON_W = BTC_ICON_WIDTH          # wallet type icon
_ACC_W       = 40                      # account "#N" text (optional)
_NET_W       = 40                      # network "test"/"sig" text (optional)

# Battery slot width on the right
_BATT_W = STATUS_BTN_WIDTH             # 60 px


def _text_width(text, font):
    """Advance width of *text* in *font*, including kerning."""
    n = len(text)
    total = 0
    for i in range(n):
        next_cp = ord(text[i + 1]) if i + 1 < n else 0
        total += font.get_glyph_width(ord(text[i]), next_cp)
    return total


def _best_font_for_name(text, max_w, max_h):
    """Return *(font, display_text)* for *text* within max_w × max_h px.

    Tries fonts from largest to smallest for a single-line fit.
    Falls back to a two-line word split at font_montserrat_16 if needed.
    """
    for font in _NAME_FONTS:
        if font.get_line_height() <= max_h and _text_width(text, font) <= max_w:
            return font, text

    f16 = lv.font_montserrat_16
    if f16.get_line_height() * 2 <= max_h:
        words = text.split()
        best_split = None
        best_balance = None
        for i in range(1, len(words)):
            left = " ".join(words[:i])
            right = " ".join(words[i:])
            lw = _text_width(left, f16)
            rw = _text_width(right, f16)
            if lw <= max_w and rw <= max_w:
                balance = max(lw, rw)
                if best_balance is None or balance < best_balance:
                    best_split = left + "\n" + right
                    best_balance = balance
        if best_split is not None:
            return f16, best_split

    return lv.font_montserrat_16, text


class TopBar(lv.obj):
    """Permanent top status bar: battery + seed/wallet context info."""

    def __init__(self, gui, height_pct=8):
        super().__init__(gui)

        self.gui = gui

        # ── Bar container style ───────────────────────────────────────────────
        self.set_width(lv.pct(100))
        self.set_height(lv.pct(height_pct))
        self.set_layout(lv.LAYOUT.NONE)   # absolute child positioning
        self.set_style_pad_all(0, 0)
        self.set_style_radius(0, 0)
        self.set_style_border_width(0, 0)
        self.set_scroll_dir(lv.DIR.NONE)

        # ── Info container (fills all space left of battery) ──────────────────
        self._info_cont = flex_row(
            self,
            width=SCREEN_WIDTH - _BATT_W,
            height=lv.pct(100),
            main_align=lv.FLEX_ALIGN.START,
        )
        self._info_cont.align(lv.ALIGN.LEFT_MID, 0, 0)
        self._info_cont.set_scroll_dir(lv.DIR.NONE)
        self._info_cont.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)

        # ── Battery (always visible, right-aligned) ───────────────────────────
        self._batt_icon = Battery(self)
        self._batt_icon.VALUE = gui.specter_state.battery_pct
        self._batt_icon.update()
        self._batt_icon.set_width(_BATT_W)
        self._batt_icon.set_height(lv.pct(100))
        self._batt_icon.align(lv.ALIGN.RIGHT_MID, 0, 0)

    # ── Public API ────────────────────────────────────────────────────────────

    def refresh(self, specter_state):
        """Rebuild info section from current state.

        Should be called whenever state changes (seed load/unload, wallet
        switch, passphrase toggle, etc.).
        """
        # Update battery
        self._batt_icon.VALUE = specter_state.battery_pct
        self._batt_icon.CHARGING = specter_state.is_charging
        self._batt_icon.update()

        # Rebuild info section
        self._info_cont.clean()

        # Locked → no info
        if specter_state.is_locked:
            return

        seeds = specter_state.loaded_seeds
        if len(seeds) != 1:
            # No seeds or more than one seed → no info
            return

        seed = seeds[0]
        self._build_seed_section(specter_state, seed)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_seed_section(self, state, seed):
        """Build the seed info area and optional wallet section."""
        info_w = SCREEN_WIDTH - _BATT_W   # total info width

        # Determine which wallet section to show
        non_default = [
            w for w in state.wallets_for_seed(seed)
            if not w.is_default_wallet()
        ]
        show_wallet = (len(non_default) == 1)
        wallet = non_default[0] if show_wallet else None

        # ── Compute budget for seed name ─────────────────────────────────────
        show_passphrase = seed.passphrase is not None
        show_warning = not getattr(seed, "is_backed_up", True)

        fixed_seed_w = (
            _FP_ICON_W + _FP_TEXT_W
            + (_PP_ICON_W if show_passphrase else 0)
            + (_WARN_ICON_W if show_warning else 0)
        )
        if show_wallet:
            fixed_wallet_w = (
                _SEP_W + _TYPE_ICON_W
                + (_ACC_W if getattr(wallet, "account", 0) != 0 else 0)
                + (_NET_W if wallet.net != "mainnet" else 0)
            )
        else:
            fixed_wallet_w = 0

        # Name width: available minus fixed elements on both sides
        seed_name_w = max(10, (info_w - fixed_seed_w - fixed_wallet_w) // 2 if show_wallet
                          else info_w - fixed_seed_w)
        wallet_name_w = max(10, (info_w - fixed_seed_w - fixed_wallet_w) // 2) if show_wallet else 0

        # ── Seed name ─────────────────────────────────────────────────────────
        seed_font, seed_text = _best_font_for_name(seed.label, seed_name_w, STATUS_BTN_HEIGHT)
        seed_lbl = lv.label(self._info_cont)
        seed_lbl.set_text(seed_text)
        seed_lbl.set_style_text_font(seed_font, 0)
        seed_lbl.set_width(seed_name_w)
        seed_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

        # ── Fingerprint: RELAY icon + first 4 hex chars ───────────────────────
        fp_img = lv.image(self._info_cont)
        fp_img.set_width(_FP_ICON_W)
        BTC_ICONS.RELAY(WHITE_HEX).add_to_parent(fp_img)

        fp_lbl = lv.label(self._info_cont)
        raw_fp = seed.get_fingerprint()
        if raw_fp.startswith("0x") or raw_fp.startswith("0X"):
            raw_fp = raw_fp[2:]
        fp_lbl.set_text(raw_fp[:4])
        fp_lbl.set_style_text_font(lv.font_montserrat_16, 0)
        fp_lbl.set_width(_FP_TEXT_W)
        fp_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

        # ── Passphrase indicator (optional, clickable) ────────────────────────
        if show_passphrase:
            pp_img = lv.image(self._info_cont)
            pp_img.set_width(_PP_ICON_W)
            pp_active = getattr(seed, "passphrase_active", False)
            pp_color = WHITE_HEX if pp_active else GREY_HEX
            BTC_ICONS.PASSWORD(pp_color).add_to_parent(pp_img)
            pp_img.add_flag(lv.obj.FLAG.CLICKABLE)
            pp_img.add_event_cb(self._toggle_passphrase_cb, lv.EVENT.CLICKED, None)

        # ── Backup warning (optional, clickable) ─────────────────────────────
        if show_warning:
            warn_img = lv.image(self._info_cont)
            warn_img.set_width(_WARN_ICON_W)
            BTC_ICONS.ALERT_CIRCLE(ORANGE_HEX).add_to_parent(warn_img)
            warn_img.add_flag(lv.obj.FLAG.CLICKABLE)
            warn_img.add_event_cb(self._backup_warning_cb, lv.EVENT.CLICKED, None)

        # ── Wallet section (optional) ─────────────────────────────────────────
        if show_wallet:
            # Separator
            sep_lbl = lv.label(self._info_cont)
            sep_lbl.set_text("/")
            sep_lbl.set_style_text_font(lv.font_montserrat_22, 0)
            sep_lbl.set_width(_SEP_W)
            sep_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

            # Wallet name
            wallet_font, wallet_text = _best_font_for_name(
                wallet.label, wallet_name_w, STATUS_BTN_HEIGHT
            )
            wallet_lbl = lv.label(self._info_cont)
            wallet_lbl.set_text(wallet_text)
            wallet_lbl.set_style_text_font(wallet_font, 0)
            wallet_lbl.set_width(wallet_name_w)
            wallet_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

            # Wallet type icon
            type_img = lv.image(self._info_cont)
            type_img.set_width(_TYPE_ICON_W)
            if not wallet.is_standard():
                type_icon = BTC_ICONS.CONSOLE
            elif wallet.isMultiSig:
                type_icon = BTC_ICONS.TWO_KEYS
            else:
                type_icon = BTC_ICONS.KEY
            matched, required = state.signing_match_count(wallet)
            key_color = WHITE_HEX if (required > 0 and matched >= required) else GREY_HEX
            type_icon(key_color).add_to_parent(type_img)

            # Multisig threshold "X/Y"
            if wallet.isMultiSig and wallet.threshold is not None:
                thresh_lbl = lv.label(self._info_cont)
                n = len(wallet.required_fingerprints)
                thresh_lbl.set_text(str(wallet.threshold) + "/" + str(n))
                thresh_lbl.set_style_text_font(lv.font_montserrat_16, 0)
                thresh_lbl.set_style_text_color(key_color, 0)

            # Account number (optional)
            account = getattr(wallet, "account", 0)
            if account != 0:
                acc_lbl = lv.label(self._info_cont)
                acc_lbl.set_text("#" + str(account))
                acc_lbl.set_style_text_font(lv.font_montserrat_16, 0)
                acc_lbl.set_width(_ACC_W)
                acc_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

            # Network (optional, only non-mainnet)
            if wallet.net != "mainnet":
                net_map = {"testnet": "test", "signet": "sig"}
                net_lbl = lv.label(self._info_cont)
                net_lbl.set_text(net_map.get(wallet.net, wallet.net))
                net_lbl.set_style_text_font(lv.font_montserrat_16, 0)
                net_lbl.set_width(_NET_W)
                net_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

    def _backup_warning_cb(self, e):
        """Show a modal explaining the backup warning and allow marking as backed up."""
        if e.get_code() != lv.EVENT.CLICKED:
            return
        seed = self.gui.specter_state.active_seed
        if seed is None:
            return

        def _mark_backed_up():
            seed.is_backed_up = True
            self.gui.refresh_ui()

        ActionModal(
            text="Your seed is not backed up!\n\nWrite down your seed phrase and store it safely.",
            buttons=[
                (None, "Close", None, None),
                (BTC_ICONS.CHECK, "I backed it up", None, _mark_backed_up),
            ],
        )

    def _toggle_passphrase_cb(self, e):
        """Toggle passphrase_active on the active seed."""
        if e.get_code() != lv.EVENT.CLICKED:
            return
        seed = self.gui.specter_state.active_seed
        if seed is None:
            return
        seed.passphrase_active = not getattr(seed, "passphrase_active", False)
        self.gui.refresh_ui()
