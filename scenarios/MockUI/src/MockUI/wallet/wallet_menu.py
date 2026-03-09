from ..basic import RED_HEX, WHITE_HEX, GenericMenu, RED, ORANGE, TITLE_ROW_HEIGHT
from ..basic.symbol_lib import BTC_ICONS
from ..basic.keyboard_text_rules import PROFILE_WALLET_NAME
import lvgl as lv


class WalletMenu(GenericMenu):
    """Menu for managing an active wallet with editable name."""

    TITLE_KEY = "MENU_MANAGE_WALLET"

    def get_menu_items(self, t, state):
        menu_items = []

        menu_items.append((None, t("WALLET_MENU_EXPLORE"), None, None, None, None))
        menu_items.append((BTC_ICONS.MENU, t("WALLET_MENU_VIEW_ADDRESSES"), "view_addresses", None, None, None))
        if (state and not state.active_wallet is None and state.active_wallet.isMultiSig):
            menu_items.append((BTC_ICONS.ADDRESS_BOOK, t("WALLET_MENU_VIEW_SIGNERS"), "view_signers", None, None, None))

        menu_items.append((None, t("WALLET_MENU_MANAGE"), None, None, None, None))
        if (state and not state.active_wallet is None and not state.active_wallet.isMultiSig):
            #Probably not needed as a fixed setting -> derivation path can be chosen in address explorer or when exporting public keys
            #menu_items.append((None, "Manage Derivation Path", "derivation_path", None, None, None))
            menu_items.append((BTC_ICONS.MNEMONIC, t("MENU_MANAGE_SEEDPHRASE"), "manage_seedphrase", None, None, None))
            menu_items.append((BTC_ICONS.PASSWORD, t("MENU_SET_PASSPHRASE"), "set_passphrase", None, None, None))
        elif (state and not state.active_wallet is None and state.active_wallet.isMultiSig):
            menu_items.append((BTC_ICONS.CONSOLE, t("WALLET_MENU_MANAGE_DESCRIPTOR"), "manage_wallet_descriptor", None, None, None))
        menu_items.append((BTC_ICONS.BITCOIN, t("WALLET_MENU_CHANGE_NETWORK"), "change_network", None, None, None))

        menu_items += [
            (None, t("WALLET_MENU_CONNECT_EXPORT"), None, None, None, None),
            (BTC_ICONS.LINK, t("MENU_CONNECT_SW_WALLET"), "connect_sw_wallet", None, None, None),
            (BTC_ICONS.EXPORT, t("WALLET_MENU_EXPORT_DATA"), "export_wallet", None, None, None)
        ]

        return menu_items

    def post_init(self, t, state):
        # Remove the default title label and replace with editable text area + edit button
        self.title.delete()

        # Text area for wallet name (editable) – lives in title_bar, centred
        self.name_textarea = lv.textarea(self.title_bar)
        self.name_textarea.set_width(270)
        self.name_textarea.set_height(TITLE_ROW_HEIGHT)
        self.name_textarea.set_style_text_font(lv.font_montserrat_28, 0)
        self.name_textarea.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        # Thicker white border so it's visually clear this field is editable
        self.name_textarea.set_style_border_width(2, lv.PART.MAIN)
        self.name_textarea.set_style_border_color(WHITE_HEX, lv.PART.MAIN)
        self.name_textarea.align(lv.ALIGN.CENTER, 0, 0)

        # Set initial text from active wallet
        wallet_name = ""
        if state and state.active_wallet:
            wallet_name = state.active_wallet.name
        self.name_textarea.set_text(wallet_name)

        # Red trash button – square, matching textarea height, to the right of textarea
        textarea_height = self.name_textarea.get_height()
        self.delete_btn = lv.button(self.title_bar)
        self.delete_btn.set_size(textarea_height, textarea_height)
        self.delete_btn.set_style_bg_color(RED_HEX, lv.PART.MAIN)
        self.delete_ico = lv.image(self.delete_btn)
        BTC_ICONS.TRASH.add_to_parent(self.delete_ico)
        self.delete_ico.center()
        self.delete_btn.align_to(self.name_textarea, lv.ALIGN.OUT_RIGHT_MID, 6, 0)

        self.original_name = ""

        # Clicking the text area shows the keyboard
        self.name_textarea.add_event_cb(lambda e: self.show_keyboard(e), lv.EVENT.CLICKED, None)

        # Trash button navigates to delete confirmation
        self.delete_btn.add_event_cb(self.make_callback("delete_wallet"), lv.EVENT.CLICKED, None)

        # Add defocus handler to text area
        self.name_textarea.add_event_cb(lambda e: self.on_defocus(e), lv.EVENT.DEFOCUSED, None)

        # Clean up keyboard if navigating away while it is open
        self.add_event_cb(lambda e: self._on_screen_delete(e), lv.EVENT.DELETE, None)

    def _on_screen_delete(self, e):
        if e.get_code() == lv.EVENT.DELETE:
            self.parent.keyboard_manager.on_owner_deleted(self)

    def show_keyboard(self, e):
        """Show the keyboard for editing wallet name."""
        if e.get_code() != lv.EVENT.CLICKED:
            return
        if self.parent.keyboard_manager.is_open_for(self):
            return  # already open

        self.original_name = self.name_textarea.get_text()

        def _on_commit(new_name):
            if self.state and self.state.active_wallet:
                self.state.active_wallet.name = new_name
                self.parent.refresh_ui()
            self.original_name = new_name

        self.parent.keyboard_manager.open(
            self,
            self.name_textarea,
            PROFILE_WALLET_NAME,
            on_commit=_on_commit,
            hide_wallet_bar=True,
        )

    def _close_keyboard(self):
        self.parent.keyboard_manager.close()

    def on_defocus(self, e):
        """Handle text area losing focus – hide keyboard and discard changes."""
        if e.get_code() != lv.EVENT.DEFOCUSED:
            return
        if not self.parent.keyboard_manager.is_open_for(self):
            return
        self.name_textarea.set_text(self.original_name)
        self._close_keyboard()
