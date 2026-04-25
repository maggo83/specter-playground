"""MenuItem — structured menu item for GenericMenu.get_menu_items().

Usage::

    MenuItem(BTC_ICONS.MENU, t("WALLET_MENU_VIEW_ADDRESSES"), "view_addresses")
    MenuItem(text=t("WALLET_MENU_EXPLORE"))               # section header
    MenuItem(BTC_ICONS.TRASH, t("DELETE"), color=RED_HEX, target=cb)
    MenuItem(BTC_ICONS.VISIBLE, t("SHOW"), "show_seedphrase",
             color=ORANGE_HEX, help_key="HELP_SHOW_SEED")
"""


class MenuItem:
    """Structured menu item for GenericMenu.

    Args:
        icon:       Icon instance or lv.SYMBOL string, or None (section header).
        text:       Display text.
        target:     None (section header), a menu_id string, or a callable.
        color:      Background color override, or None.
        size:       Height multiplier float (default 1); minimum 1.
        help_key:   i18n key for a help popup, or None.
    """

    def __init__(self, icon=None, text=None, target=None,
                 color=None, size=None, help_key=None, suffix=None):
        self.icon = icon
        self.text = text
        self.target = target
        self.color = color
        self.size = size
        self.help_key = help_key
        # suffix: list of (icon_callable_or_None, color_or_None, text_or_None) tuples
        # rendered as a right-aligned group of icons/labels inside the button.
        self.suffix = suffix
