"""Input helpers — lv.textarea wrappers with Specter default styling."""

import lvgl as lv
from ..ui_consts import TITLE_ROW_HEIGHT, WHITE_HEX

ACCEPTED_CHARS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    "0123456789!@#$%^&*()_+-=[]{}|;:,.<>?/~ "
)


def title_textarea(parent, accepted_chars=None):
    """Editable title-bar text area (font_28, centred, 2px white border).

    Intended for editable names in the title bar.

    Args:
        parent:         LVGL parent object (typically title_bar).
        accepted_chars: Character allowlist string; defaults to ACCEPTED_CHARS.
    """
    ta = lv.textarea(parent)
    ta.set_width(270)
    ta.set_height(TITLE_ROW_HEIGHT)
    ta.set_style_text_font(lv.font_montserrat_28, 0)
    ta.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
    ta.set_style_border_width(2, lv.PART.MAIN)
    ta.set_style_border_color(WHITE_HEX, lv.PART.MAIN)
    ta.align(lv.ALIGN.CENTER, 0, 0)
    ta.set_accepted_chars(accepted_chars if accepted_chars is not None else ACCEPTED_CHARS)
    return ta


def form_textarea(parent, width=None, font=None):
    """Compact form input field (font_22, height=50, 60% width by default).

    Args:
        parent: LVGL parent object (typically a flex-row form row).
        width:  Width value; defaults to lv.pct(60).
        font:   LVGL font; defaults to lv.font_montserrat_22.
    """
    ta = lv.textarea(parent)
    ta.set_width(width if width is not None else lv.pct(60))
    ta.set_height(50)
    ta.set_style_text_font(font if font is not None else lv.font_montserrat_22, 0)
    return ta
