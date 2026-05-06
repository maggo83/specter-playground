"""Image helpers — lv.image wrappers with Specter default styling."""

import lvgl as lv
from ..ui_consts import BTC_ICON_WIDTH, WHITE_HEX


def make_icon(parent, icon, color=WHITE_HEX, width=BTC_ICON_WIDTH):
    """Create an ``lv.image`` widget and attach *icon* to it.

    Args:
        parent: LVGL parent object.
        icon:   Icon factory (e.g. ``BTC_ICONS.RELAY``) called with *color*,
                or a pre-resolved ``Icon`` instance passed directly.
        color:  Hex color string passed to the icon factory.  Defaults to
                ``WHITE_HEX`` (standard Specter icon colour).  Pass ``None``
                when *icon* is already a resolved ``Icon`` instance.
        width:  Widget width in pixels.  Defaults to ``BTC_ICON_WIDTH``.

    Returns:
        The created ``lv.image`` widget.
    """
    resolved = icon(color) if color is not None else icon
    img = lv.image(parent)
    img.set_width(width)
    resolved.add_to_parent(img)
    return img
