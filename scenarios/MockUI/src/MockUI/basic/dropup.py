"""SeedDropUp / WalletDropUp — bottom-sheet selection overlays.

Both classes share the same structure:
  - Rendered above everything via layer_top (ModalOverlay)
  - Anchored at the bottom of the screen (just above the NavigationBar)
  - Grows upward; scrollable if content exceeds available height
  - Dismissed by tapping the backdrop, pressing Back, or re-tapping the
    triggering nav button

Public API (used by NavigationBar):
  dropup.is_open()  → bool
  dropup.open()     → build and show the panel
  dropup.close()    → destroy the panel
  dropup.toggle()   → open if closed, close if open
  dropup.refresh()  → rebuild card list (called after state changes)

NavigationBar height (STATUS_BAR_PCT% of 800 px = 8% × 800 = 64 px) is
passed in as *nav_bar_h*.  TopBar occupies the same height at the top.
The panel fills from the nav bar top edge upward to the top bar bottom edge.
"""

import lvgl as lv
from .modal_overlay import ModalOverlay
from .widgets.action_modal import ActionModal
from .ui_consts import (
    BTC_ICON_WIDTH, STATUS_BTN_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT,
    STATUS_BAR_PCT, WHITE_HEX, GREY_HEX, ORANGE_HEX,
    DIALOG_RADIUS, DIALOG_PAD,
)
from .symbol_lib import BTC_ICONS
from .widgets.containers import flex_row
from .widgets.btn import Btn

# ── Layout constants ──────────────────────────────────────────────────────────
_NAV_BAR_H = SCREEN_HEIGHT * STATUS_BAR_PCT // 100   # navigation bar height (px)
_TOP_BAR_H = 0                                        # no top bar
_PANEL_MAX_H = SCREEN_HEIGHT - _NAV_BAR_H             # max panel height

_CARD_H = STATUS_BTN_HEIGHT + 2 * DIALOG_PAD + 2   # height per item card (50 + 24 + 2 = 76px)
_ADD_BTN_H = STATUS_BTN_HEIGHT                       # "Add …" button height
_PANEL_PAD = 0                                       # panel outer padding

# Font helpers (reused from top_bar, inlined here to avoid circular import)
_NAME_FONTS = [
    lv.font_montserrat_22,
    lv.font_montserrat_16,
]


def _best_name_font(text, max_w, max_h):
    """Return the largest font whose glyph height fits max_h and glyph width fits max_w."""
    for font in _NAME_FONTS:
        if font.get_line_height() <= max_h:
            # approximate: average char width ≈ 10 px for font_22, 8 px for font_16
            approx_w = len(text) * font.get_glyph_width(ord('A'), 0)
            if approx_w <= max_w:
                return font
    return lv.font_montserrat_16


# ── Base class ────────────────────────────────────────────────────────────────

class _DropUp:
    """Abstract base for seed/wallet drop-up overlays."""

    def __init__(self, gui):
        self.gui = gui
        self._modal = None    # ModalOverlay instance when open

    # ── Public API ────────────────────────────────────────────────────────────

    def is_open(self):
        return self._modal is not None

    def open(self):
        if self._modal is not None:
            return
        self._modal = ModalOverlay(bg_opa=140)  # semi-transparent dim backdrop

        # Restrict the overlay to the content area only — TopBar and NavigationBar
        # must stay visible and undimmed above/below.
        _content_h = SCREEN_HEIGHT - _NAV_BAR_H #- _TOP_BAR_H 
        self._modal.overlay.set_size(SCREEN_WIDTH, _content_h)
        self._modal.overlay.set_pos(0, 0)

        # Dismiss when tapping the backdrop (outside the panel)
        self._modal.overlay.add_event_cb(self._backdrop_cb, lv.EVENT.CLICKED, None)

        # Panel: full-width strip anchored at the bottom of the content area,
        # growing upward.  panel_y is relative to the overlay (which starts at
        # 0)
        panel_h = self._compute_panel_h()
        panel_y = _content_h - panel_h

        self._panel = lv.obj(self._modal.overlay)
        self._panel.set_size(SCREEN_WIDTH, panel_h)
        self._panel.set_pos(0, panel_y)
        self._panel.set_style_radius(0, 0)
        self._panel.set_style_border_width(0, 0)
        self._panel.set_style_pad_all(0, 0)
        self._panel.set_style_pad_row(0, 0)   # zero LVGL default theme gap between flex children
        self._panel.set_layout(lv.LAYOUT.FLEX)
        self._panel.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self._panel.set_flex_align(
            lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER
        )
        # Disable horizontal scroll; enable vertical only when content overflows
        self._panel.set_scroll_dir(lv.DIR.VER)
        self._panel.set_scrollbar_mode(lv.SCROLLBAR_MODE.AUTO)
        # Stop panel clicks from bubbling up to the backdrop callback
        self._panel.add_event_cb(lambda e: e.stop_bubbling(), lv.EVENT.CLICKED, None)

        self._build_cards(self._panel)
        self._build_add_button(self._panel)

    def close(self):
        if self._modal is not None:
            self._modal.close()
            self._modal = None
            self._panel = None

    def toggle(self):
        if self.is_open():
            self.close()
        else:
            self.open()

    def refresh(self):
        """Rebuild cards in place (called after state changes)."""
        if not self.is_open():
            return
        self.close()
        self.open()

    # ── Subclass interface ────────────────────────────────────────────────────

    def _get_items(self):
        """Return list of items (seeds or wallets) to display."""
        raise NotImplementedError

    def _build_card(self, parent, item):
        """Build one item card inside parent."""
        raise NotImplementedError

    def _navigate_add(self):
        """Navigate to the add item screen."""
        raise NotImplementedError

    def _add_button_label(self):
        """Return text for the add button."""
        raise NotImplementedError

    # ── Private helpers ───────────────────────────────────────────────────────

    def _compute_panel_h(self):
        n = len(self._get_items())
        # Exact: pad_row is forced to 0 on the panel, so content = n*_CARD_H + _ADD_BTN_H
        content_h = n * _CARD_H + _ADD_BTN_H
        return min(content_h, _PANEL_MAX_H)

    def _build_cards(self, parent):
        for item in self._get_items():
            self._build_card(parent, item)

    def _build_add_button(self, parent):
        label = self._add_button_label()
        btn = Btn(
            parent,
            icon=BTC_ICONS.PLUS,
            text=label,
            size=(SCREEN_WIDTH, _ADD_BTN_H),
            callback=self._add_cb,
            font=lv.font_montserrat_16,
        )
        btn.make_transparent()

    def _add_cb(self, event=None):
        self.close()
        self._navigate_add()

    def _backdrop_cb(self, event):
        if event.get_code() == lv.EVENT.CLICKED:
            self.close()


def _card_row(parent):
    """Full-width horizontal flex row for a card, with left-aligned items."""
    row = flex_row(
        parent,
        width=SCREEN_WIDTH,
        height=_CARD_H,
        pad=DIALOG_PAD,
        main_align=lv.FLEX_ALIGN.START,
    )
    # pad_all also sets pad_column/pad_row, which adds inter-item gaps in flex
    # layout and causes horizontal overflow.  Zero it out explicitly.
    row.set_style_pad_column(0, 0)
    row.set_style_border_width(0, 0)
    row.set_style_radius(0, 0)
    # Subtle separator line at the bottom
    row.set_style_border_side(lv.BORDER_SIDE.BOTTOM, 0)
    row.set_style_border_width(0, 0)
    row.set_style_border_color(lv.color_hex(0x303030), 0)
    row.set_scroll_dir(lv.DIR.NONE)
    row.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
    return row


# ── Seed Drop-Up ──────────────────────────────────────────────────────────────

class SeedDropUp(_DropUp):
    """Drop-up overlay listing all loaded seeds with passphrase + edit buttons."""

    def _get_items(self):
        return self.gui.specter_state.loaded_seeds

    def _add_button_label(self):
        return self.gui.i18n.t("MENU_ADD_SEED")

    def _navigate_add(self):
        self.gui.show_menu("add_seed")

    def _build_card(self, parent, seed):
        row = _card_row(parent)

        # ── Seed name ─────────────────────────────────────────────────────────
        show_passphrase = seed.passphrase is not None
        name_w = (
            SCREEN_WIDTH
            - 2 * DIALOG_PAD            # row padding
            - _FP_SLOT_W                # RELAY icon + 4-char fp
            - (BTC_ICON_WIDTH if show_passphrase else 0)
            - BTC_ICON_WIDTH            # edit button
            - BTC_ICON_WIDTH            # delete button
        )
        name_font = _best_name_font(seed.label, max(10, name_w), _CARD_H)
        name_lbl = lv.label(row)
        name_lbl.set_text(seed.label)
        name_lbl.set_style_text_font(name_font, 0)
        name_lbl.set_width(max(10, name_w))
        name_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

        # ── Passphrase indicator (optional, clickable) ────────────────────────
        if show_passphrase:
            pp_active = getattr(seed, "passphrase_active", False)
            pp_color = WHITE_HEX if pp_active else GREY_HEX
            pp_img = lv.image(row)
            pp_img.set_width(BTC_ICON_WIDTH)
            BTC_ICONS.PASSWORD(pp_color).add_to_parent(pp_img)
            pp_img.add_flag(lv.obj.FLAG.CLICKABLE)

            # Capture seed in closure
            def _make_pp_cb(s):
                def _cb(e):
                    if e.get_code() == lv.EVENT.CLICKED:
                        s.passphrase_active = not getattr(s, "passphrase_active", False)
                        # Rebuild drop-up to reflect passphrase state change
                        self.refresh()
                return _cb
            pp_img.add_event_cb(_make_pp_cb(seed), lv.EVENT.CLICKED, None)

        # ── Fingerprint: RELAY icon + first 4 hex chars ───────────────────────
        fp_img = lv.image(row)
        fp_img.set_width(BTC_ICON_WIDTH)
        BTC_ICONS.RELAY(WHITE_HEX).add_to_parent(fp_img)

        fp_lbl = lv.label(row)
        raw_fp = seed.fingerprint if seed.fingerprint else "????"
        if raw_fp.startswith("0x") or raw_fp.startswith("0X"):
            raw_fp = raw_fp[2:]
        fp_lbl.set_text(raw_fp[:4])
        fp_lbl.set_style_text_font(lv.font_montserrat_16, 0)
        fp_lbl.set_width(40)
        fp_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

        # ── Edit button ───────────────────────────────────────────────────────
        def _make_edit_cb(s):
            def _cb(event=None):
                self.close()
                # Set seed as active then navigate to manage menu
                self.gui.specter_state.set_active_seed(s)
                self.gui.show_menu("manage_seedphrase")
            return _cb

        edit_btn = Btn(
            row,
            icon=BTC_ICONS.EDIT,
            size=(BTC_ICON_WIDTH, _CARD_H),
            callback=_make_edit_cb(seed),
        )
        edit_btn.make_transparent()

        # ── Delete button ─────────────────────────────────────────────────────
        def _make_delete_seed_cb(s):
            def _cb(event=None):
                t = self.gui.i18n.t

                def _do_delete():
                    self.gui.specter_state.remove_seed(s)
                    self.close()
                    self.gui.refresh_ui()

                ActionModal(
                    text=t("MODAL_DELETE_SEED_TEXT") % s.label,
                    buttons=[
                        (None,            t("COMMON_CANCEL"), None,    None),
                        (BTC_ICONS.TRASH, t("COMMON_DELETE"), ORANGE_HEX, _do_delete),
                    ],
                )
            return _cb

        del_btn = Btn(
            row,
            icon=BTC_ICONS.TRASH,
            size=(BTC_ICON_WIDTH, _CARD_H),
            callback=_make_delete_seed_cb(seed),
        )
        del_btn.make_transparent()


_FP_SLOT_W = BTC_ICON_WIDTH + 40   # RELAY icon + 4-char fingerprint label


# ── Wallet Drop-Up ────────────────────────────────────────────────────────────

class WalletDropUp(_DropUp):
    """Drop-up overlay listing all registered wallets with type + edit buttons."""

    def _get_items(self):
        return self.gui.specter_state.registered_wallets

    def _add_button_label(self):
        return self.gui.i18n.t("MENU_ADD_WALLET")

    def _navigate_add(self):
        self.gui.show_menu("add_wallet")

    def _build_card(self, parent, wallet):
        row = _card_row(parent)

        # ── Wallet type icon ──────────────────────────────────────────────────
        state = self.gui.specter_state
        if not wallet.is_standard():
            type_icon = BTC_ICONS.CONSOLE
        elif wallet.isMultiSig:
            type_icon = BTC_ICONS.TWO_KEYS
        else:
            type_icon = BTC_ICONS.KEY
        matched, required = state.signing_match_count(wallet)
        key_color = WHITE_HEX if (required > 0 and matched >= required) else GREY_HEX

        type_img = lv.image(row)
        type_img.set_width(BTC_ICON_WIDTH)
        type_icon(key_color).add_to_parent(type_img)

        # ── Wallet name ───────────────────────────────────────────────────────
        show_account = getattr(wallet, "account", 0) != 0
        show_net = wallet.net != "mainnet"
        thresh_w = 40 if wallet.isMultiSig and wallet.threshold else 0
        acc_w = 36 if show_account else 0
        net_w = 36 if show_net else 0
        name_w = (
            SCREEN_WIDTH
            - 2 * DIALOG_PAD
            - BTC_ICON_WIDTH       # type icon
            - thresh_w
            - acc_w
            - net_w
            - BTC_ICON_WIDTH       # edit button
            - BTC_ICON_WIDTH       # delete button
        )
        name_font = _best_name_font(wallet.label, max(10, name_w), _CARD_H)
        name_lbl = lv.label(row)
        name_lbl.set_text(wallet.label)
        name_lbl.set_style_text_font(name_font, 0)
        name_lbl.set_width(max(10, name_w))
        name_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

        # ── Multisig threshold ────────────────────────────────────────────────
        if wallet.isMultiSig and wallet.threshold is not None:
            thresh_lbl = lv.label(row)
            n = len(wallet.required_fingerprints)
            thresh_lbl.set_text(str(wallet.threshold) + "/" + str(n))
            thresh_lbl.set_style_text_font(lv.font_montserrat_16, 0)
            thresh_lbl.set_style_text_color(key_color, 0)
            thresh_lbl.set_width(thresh_w)
            thresh_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

        # ── Account number (optional) ─────────────────────────────────────────
        if show_account:
            acc_lbl = lv.label(row)
            acc_lbl.set_text("#" + str(wallet.account))
            acc_lbl.set_style_text_font(lv.font_montserrat_16, 0)
            acc_lbl.set_width(acc_w)
            acc_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

        # ── Network (optional) ────────────────────────────────────────────────
        if show_net:
            net_map = {"testnet": "test", "signet": "sig", "mainnet": "main"}
            net_lbl = lv.label(row)
            net_lbl.set_text(net_map.get(wallet.net, wallet.net))
            net_lbl.set_style_text_font(lv.font_montserrat_16, 0)
            net_lbl.set_width(net_w)
            net_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

        # ── Edit button ───────────────────────────────────────────────────────
        def _make_edit_cb(w):
            def _cb(event=None):
                self.close()
                self.gui.specter_state.set_active_wallet(w)
                self.gui.show_menu("manage_wallet")
            return _cb

        edit_btn = Btn(
            row,
            icon=BTC_ICONS.EDIT,
            size=(BTC_ICON_WIDTH, _CARD_H),
            callback=_make_edit_cb(wallet),
        )
        edit_btn.make_transparent()

        # ── Delete button (not shown for default wallet) ──────────────────────
        if not wallet.is_default_wallet():
            def _make_delete_wallet_cb(w):
                def _cb(event=None):
                    t = self.gui.i18n.t

                    def _do_delete():
                        self.gui.specter_state.remove_wallet(w)
                        self.close()
                        self.gui.refresh_ui()

                    ActionModal(
                        text=t("MODAL_DELETE_WALLET_TEXT") % w.label,
                        buttons=[
                            (None,            t("COMMON_CANCEL"), None,    None),
                            (BTC_ICONS.TRASH, t("COMMON_DELETE"), ORANGE_HEX, _do_delete),
                        ],
                    )
                return _cb

            del_btn = Btn(
                row,
                icon=BTC_ICONS.TRASH,
                size=(BTC_ICON_WIDTH, _CARD_H),
                callback=_make_delete_wallet_cb(wallet),
            )
            del_btn.make_transparent()
