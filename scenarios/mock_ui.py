import display
import lvgl as lv
import utime as time


from MockUI import BTN_HEIGHT, BTN_WIDTH, WalletMenu, DeviceMenu, MainMenu, SpecterState, Wallet, ActionScreen, UIState, StatusBar, SeedPhraseMenu, SecurityMenu, InterfacesMenu, BackupsMenu, FirmwareMenu, ConnectWalletsMenu, ChangeWalletMenu, AddWalletMenu, LockedMenu, GenerateSeedMenu, StorageMenu, PassphraseMenu, NavigationController

singlesig_wallet = Wallet("MyWallet", xpub="xpub6CUGRUon", isMultiSig=False)
multisig_wallet = Wallet("MyMultiSig", xpub="xpub6DUGRUon", isMultiSig=True)

specter_state = SpecterState()
specter_state.has_battery = True
specter_state.battery_pct = 100

specter_state.hasQR = True
specter_state.enabledQR = True

specter_state.hasSD = True
specter_state.enabledSD = False
specter_state.detectedSD = True

specter_state.hasSmartCard = True
specter_state.enabledSmartCard = True
specter_state.detectedSmartCard = True

#specter_state.registered_wallets.append(singlesig_wallet)
#specter_state.registered_wallets.append(multisig_wallet)
#specter_state.set_active_wallet(singlesig_wallet)
specter_state.seed_loaded = False
specter_state.active_passphrase = ""
specter_state.pin = "21"

display.init()

scr = NavigationController(specter_state)


# Needed for LVGL task handling when loaded as main script
def main():
    # Set up the default theme:
    # - disp: pointer to display (None uses the default display)
    # - color_primary: primary color of the theme (blue grey here)
    # - color_secondary: secondary color of the theme (red here)
    # - dark: True for dark mode, False for light mode (dark mode here)
    # - font: font to use (Montserrat 16 here)
    lv.theme_default_init(
        None,
        lv.palette_main(lv.PALETTE.BLUE_GREY),
        lv.palette_main(lv.PALETTE.RED),
        True,
        lv.font_montserrat_16,
    )

    lv.screen_load(scr)
    while True:
        time.sleep_ms(30)
        display.update(30)

if __name__ == '__main__':
    main()

