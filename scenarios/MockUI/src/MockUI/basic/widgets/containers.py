"""Container helpers — flex wrappers with Specter default styling.

All containers have border and padding zeroed by default.
"""

import lvgl as lv
from ..ui_consts import DIALOG_RADIUS, BIG_PAD


def _flex_container(parent, flow, width, height, pad = 0, main_align = lv.FLEX_ALIGN.START):
    cont = lv.obj(parent)
    cont.set_width(width if width is not None else lv.pct(100))
    cont.set_height(height if height is not None else lv.SIZE_CONTENT)
    cont.set_layout(lv.LAYOUT.FLEX)
    cont.set_flex_flow(flow)
    cont.set_flex_align(main_align, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
    cont.set_style_border_width(0, 0)
    cont.set_style_pad_all(pad, 0)
    return cont


def flex_col(parent, width=None, height=None, pad=0, main_align=lv.FLEX_ALIGN.START):
    """lv.obj flex-column container."""
    return _flex_container(
        parent, lv.FLEX_FLOW.COLUMN,
        width, height, pad, main_align,
    )


def flex_row(parent, width=None, height=None, pad=0, main_align=lv.FLEX_ALIGN.SPACE_EVENLY):
    """lv.obj flex-row container."""
    return _flex_container(
        parent, lv.FLEX_FLOW.ROW, 
        width, height, pad, main_align,
    )


def dialog_card(overlay, w, h, x, y, pad=BIG_PAD):
    """Centred, rounded dialog card on a ModalOverlay.

    Standard Specter dialog box: radius=8, pad=12, FLEX COLUMN CENTER,
    scrollbar off.

    Args:
        overlay: The lv.obj from a ModalOverlay instance (modal.overlay).
        w, h:    Pixel width and height.
        x, y:    Absolute position (usually centred by the caller).
        pad:     Inner padding; defaults to BIG_PAD.
    """
    dialog = lv.obj(overlay)
    dialog.set_size(w, h)
    dialog.set_pos(x, y)
    dialog.set_style_radius(DIALOG_RADIUS, 0)
    dialog.set_style_border_width(0, 0)
    dialog.set_style_pad_all(pad, 0)
    dialog.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
    dialog.set_layout(lv.LAYOUT.FLEX)
    dialog.set_flex_flow(lv.FLEX_FLOW.COLUMN)
    dialog.set_flex_align(
        lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER
    )
    return dialog
