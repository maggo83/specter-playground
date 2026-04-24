"""Label helpers — lv.label wrappers with Specter default styling."""

import lvgl as lv
from ..ui_consts import BTN_WIDTH

_DEFAULT_FONT = lv.font_montserrat_22


def set_label_color(lbl, color):
    """Set text colour of an lv.label and enable recolor markup."""
    lbl.set_style_text_color(color, 0)
    lbl.set_recolor(True)


def _make_label(parent, text, width, align, font=None, recolor=False, color=None):
    """Base label factory: create, size, font, align, colour."""
    lbl = lv.label(parent)
    lbl.set_text(text if text is not None else "")
    lbl.set_width(width)
    lbl.set_style_text_font(font if font is not None else _DEFAULT_FONT, 0)
    lbl.set_style_text_align(align, 0)
    if color is not None:
        set_label_color(lbl, color)
    elif recolor:
        lbl.set_recolor(True)
    return lbl


def body_label(parent, text, font=None, align=None, recolor=False, color=None, width=None):
    """Wrapping body/message label (font_22, CENTER, WRAP).

    Args:
        parent:  LVGL parent object.
        text:    Label text.
        font:    LVGL font; defaults to lv.font_montserrat_22.
        align:   lv.TEXT_ALIGN value; defaults to lv.TEXT_ALIGN.CENTER.
        recolor: Enable LVGL inline colour markup (#RRGGBB text#).
                 Automatically enabled when color is provided.
        color:   lv.color for the text; None = theme default.
        width:   Width value; defaults to lv.pct(100).
    """
    lbl = _make_label(parent, text,
                      width if width is not None else lv.pct(100),
                      align if align is not None else lv.TEXT_ALIGN.CENTER,
                      font, recolor, color)
    lbl.set_long_mode(lv.label.LONG_MODE.WRAP)
    return lbl


def section_header(parent, text, recolor=False, color=None):
    """Section divider label for GenericMenu (LEFT-aligned, font_22).

    Args:
        parent:  LVGL parent object.
        text:    Section header text.
        recolor: Enable LVGL inline colour markup (#RRGGBB text#).
                 Automatically enabled when color is provided.
        color:   lv.color for the text; None = theme default.
    """
    return _make_label(parent, text, lv.pct(BTN_WIDTH),
                       lv.TEXT_ALIGN.LEFT, None, recolor, color)


def form_label(parent, text, width=None, font=None, recolor=False, color=None):
    """Short left-aligned form field label (font_22, LEFT, 30% width by default).

    Args:
        parent:  LVGL parent object.
        text:    Label text.
        width:   Width value; defaults to lv.pct(30).
        font:    LVGL font; defaults to lv.font_montserrat_22.
        recolor: Enable LVGL inline colour markup (#RRGGBB text#).
                 Automatically enabled when color is provided.
        color:   lv.color for the text; None = theme default.
    """
    return _make_label(parent, text,
                       width if width is not None else lv.pct(30),
                       lv.TEXT_ALIGN.LEFT, font, recolor, color)
