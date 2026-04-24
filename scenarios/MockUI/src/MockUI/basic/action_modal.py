"""ActionModal — generic choice/confirmation modal.

Displays a text message and a row of buttons. Any button press closes the
modal; if the button has a callable attached it is invoked afterwards.

Usage::

    ActionModal(
        text="Delete wallet?\\nThis cannot be undone.",
        buttons=[
            (None,           "Cancel", None,    None),
            (BTC_ICONS.TRASH, "Delete", RED_HEX, lambda: do_delete()),
        ],
    )

Button tuple: ``(icon, label, color, callback)``
    - ``icon``     — an Icon instance (e.g. ``BTC_ICONS.TRASH``), or ``None``
    - ``label``    — button text string, or ``None`` for icon-only
    - ``color``    — LVGL color for button background, or ``None`` for default
    - ``callback`` — zero-argument callable, or ``None``

If ``buttons`` is empty a single "Close" button is added automatically.
"""

import lvgl as lv
from .modal_overlay import ModalOverlay
from .ui_consts import MODAL_WIDTH_PCT, MODAL_HEIGHT_PCT, BTN_HEIGHT


class ActionModal:
    """Generic choice modal built on top of ModalOverlay.

    Args:
        text:    Main message displayed in the dialog.
        buttons: List of ``(icon, label, color, callback)`` tuples.
                 Each element may be ``None``.  An empty list adds a
                 default "Close" button.
        bg_opa:  Backdrop opacity (0-255).  Defaults to 180.
    """

    def __init__(self, text, buttons=None, bg_opa=180):
        if buttons is None or len(buttons) == 0:
            buttons = [(None, "Close", None, None)]

        self._modal = ModalOverlay(bg_opa=bg_opa)
        sw = self._modal.screen_width
        sh = self._modal.screen_height

        dw = sw * MODAL_WIDTH_PCT // 100
        # Allow the dialog to grow with content but cap at MODAL_HEIGHT_PCT
        dh = sh * MODAL_HEIGHT_PCT // 100
        dx = (sw - dw) // 2
        dy = (sh - dh) // 2

        dialog = lv.obj(self._modal.overlay)
        dialog.set_size(dw, dh)
        dialog.set_pos(dx, dy)
        dialog.set_style_radius(8, 0)
        dialog.set_style_border_width(0, 0)
        dialog.set_style_pad_all(12, 0)
        dialog.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        dialog.set_layout(lv.LAYOUT.FLEX)
        dialog.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        dialog.set_flex_align(lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)

        # Main text
        msg_lbl = lv.label(dialog)
        msg_lbl.set_text(text)
        msg_lbl.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        msg_lbl.set_style_text_font(lv.font_montserrat_22, 0)
        msg_lbl.set_width(lv.pct(100))
        msg_lbl.set_long_mode(lv.label.LONG_MODE.WRAP)

        # Button row
        btn_row = lv.obj(dialog)
        btn_row.set_width(lv.pct(100))
        btn_row.set_height(lv.SIZE_CONTENT)
        btn_row.set_layout(lv.LAYOUT.FLEX)
        btn_row.set_flex_flow(lv.FLEX_FLOW.ROW)
        btn_row.set_flex_align(lv.FLEX_ALIGN.SPACE_EVENLY, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
        btn_row.set_style_border_width(0, 0)
        btn_row.set_style_pad_all(4, 0)

        for (icon, label, color, callback) in buttons:
            btn = lv.button(btn_row)
            btn.set_height(BTN_HEIGHT)
            btn.set_layout(lv.LAYOUT.FLEX)
            btn.set_flex_flow(lv.FLEX_FLOW.ROW)
            btn.set_flex_align(lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)

            if color is not None:
                btn.set_style_bg_color(color, lv.PART.MAIN)

            if icon is not None:
                ico_img = lv.image(btn)
                icon.add_to_parent(ico_img)

            if label is not None:
                lbl = lv.label(btn)
                lbl.set_text(label)
                lbl.set_style_text_font(lv.font_montserrat_22, 0)

            # Capture loop variables explicitly
            def _make_handler(modal, cb):
                def _handler(ev):
                    if ev.get_code() == lv.EVENT.CLICKED:
                        modal.close()
                        if cb is not None and callable(cb):
                            cb()
                return _handler

            btn.add_event_cb(_make_handler(self._modal, callback), lv.EVENT.CLICKED, None)
