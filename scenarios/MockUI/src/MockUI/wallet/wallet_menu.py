from ..basic import RED_HEX, GenericMenu, RED, ORANGE
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv


class WalletMenu(GenericMenu):
    """Menu for managing an active wallet with editable name."""

    def __init__(self, parent, *args, **kwargs):
        state = getattr(parent, "specter_state", None)
        self.parent = parent
        
        # Get translation function from i18n manager (always available via NavigationController)
        t = parent.i18n.t

        # Build menu items
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
            (BTC_ICONS.TRASH, t("WALLET_MENU_DELETE_WALLET"), "delete_wallet", RED_HEX, None, None),
            (None, t("WALLET_MENU_CONNECT_EXPORT"), None, None, None, None),
            (BTC_ICONS.LINK, t("MENU_CONNECT_SW_WALLET"), "connect_sw_wallet", None, None, None),
            (BTC_ICONS.EXPORT, t("WALLET_MENU_EXPORT_DATA"), "export_wallet", None, None, None)
        ]

        # Initialize GenericMenu with basic title (we'll customize it below)
        title = t("MENU_MANAGE_WALLET")
        super().__init__("manage_wallet", title, menu_items, parent, *args, **kwargs)

        # Remove the default title label and replace with editable text area + edit button
        self.title.delete()

        # Text area for wallet name (editable) – lives in title_bar, centred
        self.name_textarea = lv.textarea(self.title_bar)
        self.name_textarea.set_width(200)
        self.name_textarea.set_height(50)
        self.name_textarea.set_style_text_font(lv.font_montserrat_22, 0)
        self.name_textarea.set_accepted_chars("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?/~ ")
        self.name_textarea.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self.name_textarea.align(lv.ALIGN.CENTER, 0, 0)

        # Set initial text from active wallet
        wallet_name = ""
        if state and state.active_wallet:
            wallet_name = state.active_wallet.name
        self.name_textarea.set_text(wallet_name)

        # "Wallet: " label – to the left of the text area
        self.wallet_label = lv.label(self.title_bar)
        self.wallet_label.set_text("Wallet: ")
        self.wallet_label.set_style_text_font(lv.font_montserrat_22, 0)
        self.wallet_label.set_style_text_align(lv.TEXT_ALIGN.RIGHT, 0)
        self.wallet_label.align_to(self.name_textarea, lv.ALIGN.OUT_LEFT_MID, -6, 0)

        # Edit button – square, matching textarea height, to the right of textarea
        self.edit_btn = lv.button(self.title_bar)
        textarea_height = self.name_textarea.get_height()
        self.edit_btn.set_size(textarea_height, textarea_height)
        self.edit_ico = lv.image(self.edit_btn)
        BTC_ICONS.EDIT.add_to_parent(self.edit_ico)
        self.edit_ico.center()
        self.edit_btn.align_to(self.name_textarea, lv.ALIGN.OUT_RIGHT_BOTTOM, 6, 0)

        # Track keyboard state
        self.keyboard = None
        self.original_name = ""

        # Add click handlers for both text area and edit button
        self.name_textarea.add_event_cb(lambda e: self.show_keyboard(e), lv.EVENT.CLICKED, None)
        self.edit_btn.add_event_cb(lambda e: self.show_keyboard(e), lv.EVENT.CLICKED, None)
        
        # Add defocus handler to text area
        self.name_textarea.add_event_cb(lambda e: self.on_defocus(e), lv.EVENT.DEFOCUSED, None)

    def show_keyboard(self, e):
        """Show keyboard for editing wallet name."""
        if e.get_code() != lv.EVENT.CLICKED:
            return

        # If keyboard already exists, delete it first
        if self.keyboard:
            self.keyboard.delete()
            self.keyboard = None

        # Store original name for cancel/defocus
        self.original_name = self.name_textarea.get_text()

        # Create keyboard
        self.keyboard = lv.keyboard(self)
        self.keyboard.set_textarea(self.name_textarea)
        
        # Keep focus on text area
        self.name_textarea.add_state(lv.STATE.FOCUSED)
        
        # Add event handler for when OK button is pressed
        def on_keyboard_ready(e):
            if e.get_code() == lv.EVENT.READY:
                # Update wallet name in state
                new_name = self.name_textarea.get_text()
                if self.state and self.state.active_wallet:
                    self.state.active_wallet.name = new_name
                    self.parent.refresh_ui()
                # Remove focus from text area
                self.name_textarea.remove_state(lv.STATE.FOCUSED)
                # Delete keyboard
                if self.keyboard:
                    self.keyboard.delete()
                    self.keyboard = None
        
        # Add event handler for when Cancel button is pressed
        def on_keyboard_cancel(e):
            if e.get_code() == lv.EVENT.CANCEL:
                # Restore original name
                self.name_textarea.set_text(self.original_name)
                # Remove focus from text area
                self.name_textarea.remove_state(lv.STATE.FOCUSED)
                # Delete keyboard
                if self.keyboard:
                    self.keyboard.delete()
                    self.keyboard = None
        
        self.keyboard.add_event_cb(on_keyboard_ready, lv.EVENT.READY, None)
        self.keyboard.add_event_cb(on_keyboard_cancel, lv.EVENT.CANCEL, None)

    def on_defocus(self, e):
        """Handle text area losing focus - close keyboard and discard changes."""
        if e.get_code() != lv.EVENT.DEFOCUSED:
            return
        
        # If keyboard is open, close it and discard changes
        if self.keyboard:
            # Restore original name
            self.name_textarea.set_text(self.original_name)
            # Delete keyboard
            self.keyboard.delete()
            self.keyboard = None
