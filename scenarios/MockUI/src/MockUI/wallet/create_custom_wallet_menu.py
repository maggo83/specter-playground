
import lvgl as lv
import urandom
from ..basic import TitledScreen, BTN_HEIGHT, BTN_WIDTH, SWITCH_HEIGHT, SWITCH_WIDTH
from ..basic.keyboard_manager import Layout
from ..stubs import Wallet


class CreateCustomWalletMenu(TitledScreen):
    """Form to create a custom (dummy) wallet descriptor for testing.

    Allows setting wallet name, singlesig/multisig, network, fingerprints,
    and threshold so the wallet-bar signing indicators can be exercised.

    menu_id: "create_custom_wallet"
    """

    def __init__(self, parent):
        super().__init__(parent.i18n.t("ADD_WALLET_CREATE_CUSTOM"), parent)
        t = self.i18n.t

        self.body.set_layout(lv.LAYOUT.FLEX)
        self.body.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.body.set_flex_align(lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)

        ROW_H = 60

        # ── Wallet name ──────────────────────────────────────────────
        name_row = self._make_row(ROW_H)
        name_lbl = lv.label(name_row)
        name_lbl.set_text(t("COMMON_NAME"))
        name_lbl.set_width(lv.pct(25))
        name_lbl.set_style_text_font(lv.font_montserrat_22, 0)

        self.name_ta = lv.textarea(name_row)
        self.name_ta.set_text(t("COMMON_WALLET") + " " + str(urandom.randint(1, 99)))
        self.name_ta.set_width(lv.pct(65))
        self.name_ta.set_height(46)
        self.name_ta.set_style_text_font(lv.font_montserrat_22, 0)
        kb = lambda e: self.gui.keyboard_manager.bind(self.name_ta, Layout.FULL)
        self.name_ta.add_event_cb(kb, lv.EVENT.CLICKED, None)

        # ── Multisig toggle ──────────────────────────────────────────
        ms_row = self._make_row(ROW_H)
        ms_lbl = lv.label(ms_row)
        ms_lbl.set_text(t("COMMON_MULTISIG"))
        ms_lbl.set_width(lv.pct(50))
        ms_lbl.set_style_text_font(lv.font_montserrat_22, 0)

        self.ms_sw = lv.switch(ms_row)
        self.ms_sw.set_size(SWITCH_HEIGHT, SWITCH_WIDTH)
        self.ms_sw.add_event_cb(lambda e: self._on_multisig_toggle(e), lv.EVENT.VALUE_CHANGED, None)

        # ── Threshold (visible only for multisig) ────────────────────
        self.thresh_row = self._make_row(ROW_H)
        th_lbl = lv.label(self.thresh_row)
        th_lbl.set_text(t("ADD_WALLET_THRESHOLD"))
        th_lbl.set_width(lv.pct(50))
        th_lbl.set_style_text_font(lv.font_montserrat_22, 0)

        self.thresh_ta = lv.textarea(self.thresh_row)
        self.thresh_ta.set_text("2")
        self.thresh_ta.set_width(lv.pct(30))
        self.thresh_ta.set_height(46)
        self.thresh_ta.set_accepted_chars("0123456789")
        self.thresh_ta.set_style_text_font(lv.font_montserrat_22, 0)
        kb2 = lambda e: self.gui.keyboard_manager.bind(self.thresh_ta, Layout.FULL)
        self.thresh_ta.add_event_cb(kb2, lv.EVENT.CLICKED, None)
        self.thresh_row.add_flag(lv.obj.FLAG.HIDDEN)  # hidden until multisig

        # ── Extra fingerprints (for multisig cosigners) ──────────────
        self.fp_row = self._make_row(ROW_H)
        fp_lbl = lv.label(self.fp_row)
        fp_lbl.set_text(t("ADD_WALLET_SIGNERS"))
        fp_lbl.set_width(lv.pct(35))
        fp_lbl.set_style_text_font(lv.font_montserrat_16, 0)

        self.fp_ta = lv.textarea(self.fp_row)
        self.fp_ta.set_text("aabbccdd,11223344")
        self.fp_ta.set_width(lv.pct(55))
        self.fp_ta.set_height(46)
        self.fp_ta.set_accepted_chars("0123456789abcdef,")
        self.fp_ta.set_style_text_font(lv.font_montserrat_16, 0)
        kb3 = lambda e: self.gui.keyboard_manager.bind(self.fp_ta, Layout.FULL)
        self.fp_ta.add_event_cb(kb3, lv.EVENT.CLICKED, None)
        self.fp_row.add_flag(lv.obj.FLAG.HIDDEN)

        # ── Network toggle ───────────────────────────────────────────
        net_row = self._make_row(ROW_H)
        net_lbl = lv.label(net_row)
        net_lbl.set_text("Testnet")
        net_lbl.set_width(lv.pct(50))
        net_lbl.set_style_text_font(lv.font_montserrat_22, 0)

        self.net_sw = lv.switch(net_row)
        self.net_sw.set_size(SWITCH_HEIGHT, SWITCH_WIDTH)

        # ── Custom toggle ───────────────────────────────────────────
        custom_row = self._make_row(ROW_H)
        custom_lbl = lv.label(custom_row)
        custom_lbl.set_text(t("ADD_WALLET_CUSTOM"))
        custom_lbl.set_width(lv.pct(50))
        custom_lbl.set_style_text_font(lv.font_montserrat_22, 0)

        self.custom_sw = lv.switch(custom_row)
        self.custom_sw.set_size(SWITCH_HEIGHT, SWITCH_WIDTH)

        # ── Create button ────────────────────────────────────────────
        btn_row = self._make_row(80)
        self.create_btn = lv.button(btn_row)
        self.create_btn.set_width(lv.pct(BTN_WIDTH))
        self.create_btn.set_height(BTN_HEIGHT)
        clbl = lv.label(self.create_btn)
        clbl.set_text(t("COMMON_CREATE"))
        clbl.set_style_text_font(lv.font_montserrat_22, 0)
        clbl.center()
        self.create_btn.add_event_cb(lambda e: self._on_create(e), lv.EVENT.CLICKED, None)

    # ── helpers ──────────────────────────────────────────────────────

    def _make_row(self, height):
        row = lv.obj(self.body)
        row.set_width(lv.pct(100))
        row.set_height(height)
        row.set_layout(lv.LAYOUT.FLEX)
        row.set_flex_flow(lv.FLEX_FLOW.ROW)
        row.set_flex_align(lv.FLEX_ALIGN.SPACE_BETWEEN, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
        row.set_style_border_width(0, 0)
        row.set_style_pad_all(4, 0)
        row.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        return row

    def _on_multisig_toggle(self, e):
        if self.ms_sw.has_state(lv.STATE.CHECKED):
            self.thresh_row.remove_flag(lv.obj.FLAG.HIDDEN)
            self.fp_row.remove_flag(lv.obj.FLAG.HIDDEN)
        else:
            self.thresh_row.add_flag(lv.obj.FLAG.HIDDEN)
            self.fp_row.add_flag(lv.obj.FLAG.HIDDEN)

    def _on_create(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return

        name = self.name_ta.get_text()
        is_multi = self.ms_sw.has_state(lv.STATE.CHECKED)
        net = "testnet" if self.net_sw.has_state(lv.STATE.CHECKED) else "mainnet"
        is_custom = self.custom_sw.has_state(lv.STATE.CHECKED)

        # Build fingerprint list
        fps = []
        # Always include the active seed's fingerprint
        if self.state and self.state.active_seed:
            fps.append(self.state.active_seed.fingerprint)

        threshold = None
        if is_multi:
            # Parse extra cosigner fingerprints
            raw = self.fp_ta.get_text().strip()
            if raw:
                for fp in raw.split(","):
                    fp = fp.strip()
                    if fp and fp not in fps:
                        fps.append(fp)
            try:
                threshold = int(self.thresh_ta.get_text())
            except Exception:
                threshold = 2

        # Build a dummy descriptor string
        if is_custom:
            desc = "fancy script"
        elif is_multi:
            desc = "wsh(sortedmulti(%d,%s))" % (threshold, ",".join(fps))
        else:
            fp0 = fps[0] if fps else "00000000"
            desc = "wpkh([%s/84h/0h/0h]xpub...)" % fp0

        wallet = Wallet(
            label=name,
            descriptor=desc,
            isMultiSig=is_multi,
            net=net,
            required_fingerprints=fps,
            threshold=threshold,
        )
        self.state.register_wallet(wallet)
        self.state.set_active_wallet(wallet)

        # Navigate to main
        if hasattr(self.gui, 'ui_state') and self.gui.ui_state:
            self.gui.ui_state.clear_history()
            self.gui.ui_state.current_menu_id = "main"
        self.on_navigate(None)
