"""SelectAndManageBar — generic "previous / switch-add / info / manage / next" bar.

Used twice: once for Seeds, once for Wallets.

Layout (left-to-right, full width, SELECT_BAR_PCT% height):
    ┌────────────────────────────────────────────────────────────┐
    │ [◀] [▾/+]  <info section (fills centre)>  [✎] [▶]        │
    └────────────────────────────────────────────────────────────┘

Left side (fixed):
    prev_btn  — CARET_LEFT, grey when no previous element
    switch_btn — PLUS when list empty, CARET_DOWN when list has items
                 → opens the corresponding switch_add_<type> menu

Centre (flex-grow):
    Type-specific info rendered by subclass via _build_info(parent, item)

Right side (fixed):
    manage_btn — EDIT icon → opens manage menu for active item
    next_btn   — CARET_RIGHT, grey when no next element

When the list is empty (no items) the entire info section and manage/next
buttons are hidden and only the switch_btn (PLUS) is shown.
"""

import lvgl as lv
from .ui_consts import (
    STATUS_BTN_HEIGHT, STATUS_BTN_WIDTH, BTC_ICON_WIDTH,
    GREY_HEX, GREEN_HEX, WHITE_HEX, ORANGE_HEX, SCREEN_WIDTH,
)
from .symbol_lib import BTC_ICONS
from .widgets.btn import Btn
from .widgets.containers import flex_row
from .widgets.action_modal import ActionModal

# ── Info-section layout constants ────────────────────────────────────────────
# info_w = SCREEN_WIDTH - 2 * _OUTER_BTN_W(45) - 2 * _NAV_BTN_W(60) = 270 px
_INFO_W = SCREEN_WIDTH - 2 * (STATUS_BTN_WIDTH * 3 // 4) - 2 * STATUS_BTN_WIDTH
# Right group (icon + text label) always flush with the manage button.
_RIGHT_W = 90           # BTC_ICON_WIDTH(42) + _RIGHT_TEXT_W(48) — sized for font_montserrat_16
_RIGHT_TEXT_W = _RIGHT_W - BTC_ICON_WIDTH   # 48 — fp / net-type label width
# Left group — name + optional elements, total = _INFO_W - _RIGHT_W = 180 px
_LEFT_W = _INFO_W - _RIGHT_W


# ── Name-label font helpers ───────────────────────────────────────────────────
# Fonts available on hardware (from lv_conf.h), ordered largest → smallest.
# font_montserrat_16 is the minimum — matches what was used before.
_NAME_FONTS = [
    lv.font_montserrat_28,
    lv.font_montserrat_22,
    lv.font_montserrat_16,
]


def _text_width(text, font):
    """Return advance width (px) of *text* in *font*, including kerning."""
    n = len(text)
    total = 0
    for i in range(n):
        next_cp = ord(text[i + 1]) if i + 1 < n else 0
        total += font.get_glyph_width(ord(text[i]), next_cp)
    return total


def _best_font_for_name(text, max_w, max_h):
    """Return *(font, display_text)* for *text* within max_w × max_h px.

    Tries fonts from largest to smallest for a single-line fit.
    If even font_montserrat_16 doesn't fit single-line, tries splitting the
    text at word boundaries into two lines (both lines ≤ max_w) — two lines of
    font_16 require only 36 px height which fits the 50 px bar.
    Falls back to *(font_16, original_text)* if no split works; label clips.
    """
    for font in _NAME_FONTS:
        if font.get_line_height() <= max_h and _text_width(text, font) <= max_w:
            return font, text

    # Try two-line word-split at font_montserrat_16
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


def wallet_key_color(specter_state, wallet):
    """Return the icon colour for a wallet's key icon.

    white  — all required signing keys are loaded (wallet is signable)
    grey   — not all required keys are present
    """
    matched, required = specter_state.signing_match_count(wallet)
    return WHITE_HEX if (required > 0 and matched >= required) else GREY_HEX


class SelectAndManageBar(lv.obj):
    """Generic select-and-manage bar. Subclass and override _build_info()."""

    # Width of inner nav buttons (switch / manage)
    _NAV_BTN_W = STATUS_BTN_WIDTH
    # Width of outer nav buttons (prev / next) — narrower to save space
    _OUTER_BTN_W = STATUS_BTN_WIDTH * 3 // 4

    def __init__(self, gui, height_pct=8):
        super().__init__(gui)

        self.gui = gui

        self.set_width(lv.pct(100))
        self.set_height(lv.pct(height_pct))
        # No flex on the bar itself — absolute positioning for the buttons so
        # LVGL theme gaps cannot push them apart.
        self.set_style_pad_all(0, 0)
        self.set_style_radius(0, 0)
        self.set_style_border_width(0, 0)
        self.set_scroll_dir(lv.DIR.NONE)

        wi = self._NAV_BTN_W    # inner buttons: switch, manage (full width)
        wo = self._OUTER_BTN_W  # outer buttons: prev, next (3/4 width)
        h = STATUS_BTN_HEIGHT

        # ── LEFT: prev at x=0, switch at x=wo ───────────────────────────────
        self.prev_btn = Btn(
            self, icon=BTC_ICONS.CARET_LEFT, size=(wo, h), callback=self._prev_cb,
        )
        self.prev_btn.make_transparent()
        self.prev_btn.align(lv.ALIGN.LEFT_MID, 0, 0)

        self.switch_btn = Btn(
            self, icon=BTC_ICONS.PLUS, size=(wi, h), callback=self._switch_cb,
        )
        self.switch_btn.make_transparent()
        self.switch_btn.align(lv.ALIGN.LEFT_MID, wo, 0)

        # ── RIGHT: next at far right, manage just left of it ─────────────────
        self.next_btn = Btn(
            self, icon=BTC_ICONS.CARET_RIGHT, size=(wo, h), callback=self._next_cb,
        )
        self.next_btn.make_transparent()
        self.next_btn.align(lv.ALIGN.RIGHT_MID, 0, 0)

        self.manage_btn = Btn(
            self, icon=BTC_ICONS.EDIT_OUTLINE, size=(wi, h), callback=self._manage_cb,
        )
        self.manage_btn.make_transparent()
        self.manage_btn.align(lv.ALIGN.RIGHT_MID, -wo, 0)

        # ── CENTRE: info section between the two button pairs ─────────────────
        info_x = wo + wi
        info_w = SCREEN_WIDTH - wo - wi - wi - wo
        self.info_section = flex_row(
            self, width=info_w, height=lv.pct(100),
            main_align=lv.FLEX_ALIGN.START,
        )
        self.info_section.align(lv.ALIGN.LEFT_MID, info_x, 0)

    # ── Subclass hooks ────────────────────────────────────────────────────────

    def get_items(self):
        """Return the list of items (seeds or wallets). Override in subclass."""
        return []

    def get_active(self):
        """Return the currently active item or None. Override in subclass."""
        return None

    def set_active(self, item):
        """Set the active item and trigger a GUI refresh. Override in subclass."""
        pass

    def get_add_menu_id(self):
        """Return the menu_id for the add-item menu (used when 0 or 1 items). Override."""
        return None

    def get_switch_menu_id(self):
        """Return the menu_id for the switch/select menu (used when 2+ items). Override."""
        return None

    def get_manage_menu_id(self):
        """Return the menu_id string for the manage menu. Override in subclass."""
        return None

    def get_manage_menu_ids(self):
        """Return frozenset of all menu IDs that belong to the manage subtree.

        Used by _manage_cb to detect when we are already inside the manage
        flow so pressing the button again closes / navigates back.
        Override in subclass.
        """
        m = self.get_manage_menu_id()
        return frozenset([m]) if m else frozenset()

    def _show_nav_arrows(self, items):
        """Whether prev/next navigation arrows should be shown. Override in subclass."""
        return True

    def _use_plus_icon(self, items):
        """Whether the switch button should show PLUS (vs CARET_DOWN). Override in subclass."""
        return len(items) <= 1

    def _build_info(self, parent, item):
        """Populate the info section for the given active item.

        Override in subclass. Default shows the item label only.
        """
        lbl = lv.label(parent)
        lbl.set_text(item.label if item is not None else "")
        lbl.set_style_text_font(lv.font_montserrat_16, 0)

    # ── Button callbacks ─────────────────────────────────────────────────────

    def _prev_cb(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return
        items = self.get_items()
        active = self.get_active()
        if not items or active is None or active not in items:
            return
        idx = items.index(active)
        if idx > 0:
            self.set_active(items[idx - 1])
            # Slide content to reveal the previous item from the left
            self.gui.refresh_ui_animated("left")

    def _next_cb(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return
        items = self.get_items()
        active = self.get_active()
        if not items or active is None or active not in items:
            return
        idx = items.index(active)
        if idx < len(items) - 1:
            self.set_active(items[idx + 1])
            # Slide content to reveal the next item from the right
            self.gui.refresh_ui_animated("right")

    def _switch_cb(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return
        items = self.get_items()
        current = (
            self.gui.ui_state.current_menu_id if self.gui.ui_state else None
        )
        switch_menu = self.get_switch_menu_id()
        if current == switch_menu:
            # Switch menu already open: CARET_UP = cancel / go back
            self.gui.show_menu(None)
            return
        if self._use_plus_icon(items):
            # PLUS icon: go directly to add menu
            add_menu = self.get_add_menu_id()
            if add_menu:
                self.gui.show_menu(add_menu)
        else:
            # CARET_DOWN icon: open switch/select menu
            if switch_menu:
                self.gui.show_menu(switch_menu)

    def _manage_cb(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return
        menu_id = self.get_manage_menu_id()
        if not menu_id:
            return
        current = self.gui.ui_state.current_menu_id if self.gui.ui_state else None
        manage_menus = self.get_manage_menu_ids()
        if current == menu_id:
            # Already on the manage menu root — close it
            self.gui.show_menu(None)
        elif current in manage_menus:
            # Inside a manage sub-menu — pop history back to manage root,
            # then close that too (like settings button behaviour)
            while (self.gui.ui_state.history
                   and self.gui.ui_state.history[-1] != menu_id):
                self.gui.ui_state.pop_menu()
            self.gui.show_menu(None)
        else:
            self.gui.show_menu(menu_id)

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self, state):
        """Rebuild info section and update button states from current state."""
        items = self.get_items()
        active = self.get_active()
        has_items = len(items) > 0
        current = (
            self.gui.ui_state.current_menu_id if self.gui.ui_state else None
        )

        # switch_btn icon:
        #   on switch menu already open  → CARET_UP  (cancel)
        #   otherwise use _use_plus_icon → PLUS or CARET_DOWN
        if current == self.get_switch_menu_id():
            self.switch_btn.update_icon(BTC_ICONS.CARET_UP)
        elif self._use_plus_icon(items):
            self.switch_btn.update_icon(BTC_ICONS.PLUS)
        else:
            self.switch_btn.update_icon(BTC_ICONS.CARET_DOWN)

        # manage_btn icon: filled EDIT when in that manage submenu, outline otherwise
        manage_active = current in self.get_manage_menu_ids()
        self.manage_btn.update_icon(
            BTC_ICONS.EDIT if manage_active else BTC_ICONS.EDIT_OUTLINE
        )

        # Reposition buttons and info_section depending on arrow visibility.
        # Since the bar uses absolute positioning, we must physically move
        # widgets — opacity=TRANSP just hides pixels but does NOT free space.
        show_arrows = self._show_nav_arrows(items)
        wo = self._OUTER_BTN_W
        wi = self._NAV_BTN_W
        if show_arrows:
            # Full layout: [prev(wo)][switch(wi)] <info> [manage(wi)][next(wo)]
            self.prev_btn.set_style_opa(lv.OPA.COVER, 0)
            self.next_btn.set_style_opa(lv.OPA.COVER, 0)
            self.switch_btn.align(lv.ALIGN.LEFT_MID, wo, 0)
            self.manage_btn.align(lv.ALIGN.RIGHT_MID, -wo, 0)
            info_x = wo + wi
            info_w = SCREEN_WIDTH - 2 * wo - 2 * wi
        else:
            # Compact layout: [switch(wi)] <info> [manage(wi)]  (no prev/next)
            self.prev_btn.set_style_opa(lv.OPA.TRANSP, 0)
            self.next_btn.set_style_opa(lv.OPA.TRANSP, 0)
            self.switch_btn.align(lv.ALIGN.LEFT_MID, 0, 0)
            self.manage_btn.align(lv.ALIGN.RIGHT_MID, 0, 0)
            info_x = wi
            info_w = SCREEN_WIDTH - 2 * wi
        self.info_section.set_width(info_w)
        self.info_section.align(lv.ALIGN.LEFT_MID, info_x, 0)
        self._current_info_w = info_w

        # active_in_cycle: whether active is in the filtered cycling list
        active_in_cycle = active is not None and active in items

        if active is not None:
            # Always show info + manage for the active item, even if it's outside
            # the cycling subset (e.g. a wallet from another seed was selected).
            _grey = GREY_HEX
            _white = WHITE_HEX
            if show_arrows:
                if active_in_cycle:
                    idx = items.index(active)
                    prev_color = _grey if idx == 0 else _white
                    next_color = _grey if idx == len(items) - 1 else _white
                else:
                    prev_color = _grey
                    next_color = _grey
                self.prev_btn.update_icon(BTC_ICONS.CARET_LEFT, color=prev_color)
                self.next_btn.update_icon(BTC_ICONS.CARET_RIGHT, color=next_color)

            # rebuild info section
            self.info_section.clean()
            self._build_info(self.info_section, active)

            self.info_section.set_style_opa(lv.OPA.COVER, 0)
            self.manage_btn.set_style_opa(lv.OPA.COVER, 0)
        else:
            # No active item — hide everything except switch_btn
            self.info_section.set_style_opa(lv.OPA.TRANSP, 0)
            self.manage_btn.set_style_opa(lv.OPA.TRANSP, 0)
            self.next_btn.set_style_opa(lv.OPA.TRANSP, 0)
            self.prev_btn.set_style_opa(lv.OPA.TRANSP, 0)


# ── Concrete subclass: Seeds ──────────────────────────────────────────────────

class SelectAndManageSeedsBar(SelectAndManageBar):
    """Select-and-manage bar for loaded seeds.

    Info section (left to right):
        seed name | RELAY icon + first 4 chars of fingerprint
        | PASSWORD icon (white=active, grey=inactive, hidden if no passphrase)
        | ALERT_CIRCLE warning (if not backed up)
    """

    def get_items(self):
        """Return seeds to cycle through.

        If the active wallet is a multisig and at least 2 of its required
        keys are currently loaded, restrict cycling to only the seeds that
        belong to that wallet (so left/right nav stays in context).
        Otherwise return all loaded seeds.
        """
        state = self.gui.specter_state
        wallet = state.active_wallet
        if (wallet and wallet.isMultiSig and not wallet.is_default_wallet()):
            seeds_for_wallet = state.seeds_for_wallet(wallet)
            if seeds_for_wallet and len(seeds_for_wallet) >= 2:
                return seeds_for_wallet
        return state.loaded_seeds

    def get_active(self):
        return self.gui.specter_state.active_seed

    def set_active(self, item):
        self.gui.specter_state.set_active_seed(item)

    def get_add_menu_id(self):
        return "add_seed"

    def get_switch_menu_id(self):
        return "switch_add_seeds"

    def get_manage_menu_id(self):
        return "manage_seedphrase"

    def get_manage_menu_ids(self):
        return frozenset([
            "manage_seedphrase", "store_seedphrase", "clear_seedphrase",
            "set_passphrase",
        ])

    def _show_nav_arrows(self, items):
        """Hide prev/next when only one seed is loaded — no point cycling."""
        return len(items) > 1

    # _NAME_W is no longer a fixed constant — name width is computed dynamically
    # in _build_info depending on which optional elements are visible.

    def _build_info(self, parent, seed):
        multi_seed = len(self.gui.specter_state.loaded_seeds) > 1
        # Available info width (expanded when nav arrows are hidden for single seed)
        info_w = getattr(self, '_current_info_w', _INFO_W)
        # Right group (fp) only shown for multi-seed; adjust left area accordingly
        available_left = info_w - (_RIGHT_W if multi_seed else 0)
        # ── Optional elements (between name and right group) ─────────────────
        show_passphrase = seed.passphrase is not None
        show_warning = not seed.is_backed_up
        opt_w = (
            (BTC_ICON_WIDTH if show_passphrase else 0)
            + (BTC_ICON_WIDTH if show_warning else 0)
        )
        name_w = available_left - opt_w

        # ── Name (left, dynamic width) ────────────────────────────────────────
        font, name_text = _best_font_for_name(seed.label, name_w, STATUS_BTN_HEIGHT)
        name_lbl = lv.label(parent)
        name_lbl.set_text(name_text)
        name_lbl.set_style_text_font(font, 0)
        name_lbl.set_width(name_w)
        name_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

        # ── Passphrase indicator (optional) ───────────────────────────────────
        if show_passphrase:
            pp_img = lv.image(parent)
            pp_img.set_width(BTC_ICON_WIDTH)
            pp_color = WHITE_HEX if seed.passphrase_active else GREY_HEX
            BTC_ICONS.PASSWORD(pp_color).add_to_parent(pp_img)
            pp_img.add_flag(lv.obj.FLAG.CLICKABLE)
            pp_img.add_event_cb(self._toggle_passphrase_cb, lv.EVENT.CLICKED, None)

        # ── Backup warning (optional) ─────────────────────────────────────────
        if show_warning:
            warn_img = lv.image(parent)
            warn_img.set_width(BTC_ICON_WIDTH)
            BTC_ICONS.ALERT_CIRCLE(ORANGE_HEX).add_to_parent(warn_img)
            warn_img.add_flag(lv.obj.FLAG.CLICKABLE)
            warn_img.add_event_cb(self._backup_warning_cb, lv.EVENT.CLICKED, None)
        # ── Right group: RELAY icon + fingerprint — only when multiple seeds loaded
        if len(self.gui.specter_state.loaded_seeds) > 1:
            right_cont = flex_row(parent, width=_RIGHT_W, height=lv.pct(100),
                                  main_align=lv.FLEX_ALIGN.START)
            fp_icon_img = lv.image(right_cont)
            fp_icon_img.set_width(BTC_ICON_WIDTH)
            BTC_ICONS.RELAY(WHITE_HEX).add_to_parent(fp_icon_img)

            fp_lbl = lv.label(right_cont)
            raw_fp = seed.fingerprint if seed.fingerprint else "????"
            if raw_fp.startswith("0x") or raw_fp.startswith("0X"):
                raw_fp = raw_fp[2:]
            fp_lbl.set_text(raw_fp[:4])
            fp_lbl.set_style_text_font(lv.font_montserrat_16, 0)
            fp_lbl.set_width(_RIGHT_TEXT_W)
            fp_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

    def _toggle_passphrase_cb(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return
        seed = self.gui.specter_state.active_seed
        if seed is None:
            return
        seed.passphrase_active = not seed.passphrase_active
        self.gui.refresh_ui()

    def _backup_warning_cb(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return
        seed = self.gui.specter_state.active_seed
        if seed is None:
            return
        t = self.gui.i18n.t

        def _mark_backed_up():
            seed.is_backed_up = True
            self.gui.refresh_ui()

        ActionModal(
            text=t("MODAL_BACKUP_WARNING_TEXT"),
            buttons=[
                (None, t("COMMON_OK"), None, None),
                (BTC_ICONS.CHECK, t("MODAL_BACKUP_CONFIRMED_BTN"), None, _mark_backed_up),
            ],
        )


# ── Concrete subclass: Wallets ────────────────────────────────────────────────

class SelectAndManageWalletsBar(SelectAndManageBar):
    """Select-and-manage bar for registered wallets.

    Info section (left to right):
        wallet name | type icon (KEY=singlesig, TWO_KEYS=multisig)
        | account "#N" | net type text
    """

    def get_items(self):
        """Return wallets for the active seed only (plus Default Wallet).

        Cycling left/right through wallets is limited to wallets that
        include the currently selected seed, so the user stays in context.
        """
        state = self.gui.specter_state
        seed = state.active_seed
        if seed is not None:
            wallets = state.wallets_for_seed(seed)
            return wallets if wallets else state.registered_wallets
        return state.registered_wallets

    def get_active(self):
        return self.gui.specter_state.active_wallet

    def set_active(self, item):
        self.gui.specter_state.set_active_wallet(item)

    def get_add_menu_id(self):
        return "add_wallet"

    def get_switch_menu_id(self):
        return "switch_add_wallets"

    def get_manage_menu_id(self):
        return "manage_wallet"

    def get_manage_menu_ids(self):
        return frozenset(["manage_wallet", "manage_wallet_descriptor"])

    # Account column width — 1 digit at font_28 (39 px), 2 digits at font_16 (33 px).
    _ACC_W = 40

    def _use_plus_icon(self, items):
        """Show PLUS only when no user-created wallets exist."""
        return all(w.is_default_wallet() for w in self.gui.specter_state.registered_wallets)

    @property
    def _show_account_col(self):
        """True when at least one wallet has a non-zero account number."""
        return any(w.account != 0 for w in self.get_items())

    @property
    def _show_net_col(self):
        """True when at least one registered wallet uses a non-mainnet network."""
        return any(w.net != "mainnet" for w in self.gui.specter_state.registered_wallets)

    def _build_info(self, parent, wallet):
        # ── Optional element: account number ─────────────────────────────────
        show_account = self._show_account_col
        opt_w = self._ACC_W if show_account else 0
        name_w = _LEFT_W - opt_w  # expands to full _LEFT_W when not shown

        # ── Name (left, dynamic width) ────────────────────────────────────────
        font, name_text = _best_font_for_name(wallet.label, name_w, STATUS_BTN_HEIGHT)
        name_lbl = lv.label(parent)
        name_lbl.set_text(name_text)
        name_lbl.set_style_text_font(font, 0)
        name_lbl.set_width(name_w)
        name_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

        # ── Account number (optional) ─────────────────────────────────────────
        if show_account:
            acc_text = "#" + str(wallet.account)
            acc_font, acc_display = _best_font_for_name(acc_text, self._ACC_W, STATUS_BTN_HEIGHT)
            acc_lbl = lv.label(parent)
            acc_lbl.set_text(acc_display)
            acc_lbl.set_style_text_font(acc_font, 0)
            acc_lbl.set_width(self._ACC_W)
            acc_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

        # ── Right group: type icon + net label — fixed _RIGHT_W, right-flush ──
        right_cont = flex_row(parent, width=_RIGHT_W, height=lv.pct(100),
                              main_align=lv.FLEX_ALIGN.START)
        type_img = lv.image(right_cont)
        type_img.set_width(BTC_ICON_WIDTH)
        if not wallet.is_standard():  # custom script
            type_icon = BTC_ICONS.CONSOLE
        elif wallet.isMultiSig:
            type_icon = BTC_ICONS.TWO_KEYS
        else:
            type_icon = BTC_ICONS.KEY
        # White when all required keys loaded, grey otherwise
        key_color = wallet_key_color(self.gui.specter_state, wallet)
        type_icon(key_color).add_to_parent(type_img)

        if self._show_net_col:
            net_lbl = lv.label(right_cont)
            net_map = {"mainnet": "main", "testnet": "test", "signet": "sig"}
            net_lbl.set_text(net_map.get(wallet.net, wallet.net))
            net_lbl.set_style_text_font(lv.font_montserrat_16, 0)
            net_lbl.set_width(_RIGHT_TEXT_W)
            net_lbl.set_long_mode(lv.label.LONG_MODE.CLIP)

