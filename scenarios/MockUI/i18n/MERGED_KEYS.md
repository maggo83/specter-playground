# Merged Translation Keys

This document summarizes the translation key consolidation performed to reduce translator workload by eliminating duplicate strings.

## Rationale

Many strings were defined multiple times for different uses, requiring translators to translate identical text repeatedly. These have been merged into single shared keys used consistently across all UI components.

## Menu Entry/Title Mergers (MENU_* prefix)

These keys consolidate menu entries in parent menus with submenu titles:

| Merged Key | Old Keys | Usage |
|-----------|----------|-------|
| `MENU_MANAGE_WALLET` | `MAIN_MENU_MANAGE_WALLET`, `WALLET_MENU_TITLE` | Main menu entry + Wallet menu title |
| `MENU_MANAGE_SEEDPHRASE` | `WALLET_MENU_MANAGE_SEEDPHRASE` | Wallet menu entry + Seedphrase menu title |
| `MENU_SET_PASSPHRASE` | `WALLET_MENU_SET_PASSPHRASE` | Wallet menu entry + Passphrase screen title |
| `MENU_CONNECT_SW_WALLET` | `WALLET_MENU_CONNECT_SW_WALLET` | Wallet menu entry + Connect wallets menu title |
| `MENU_ADD_WALLET` | `MAIN_MENU_ADD_WALLET`, `CHANGE_WALLET_ADD` | Main menu entry + Add wallet menu entry |
| `MENU_MANAGE_BACKUPS` | `DEVICE_MENU_BACKUPS` | Device menu entry + Backups menu title |
| `MENU_MANAGE_FIRMWARE` | `DEVICE_MENU_FIRMWARE` | Device menu entry + Firmware menu title |
| `MENU_MANAGE_SECURITY` | `DEVICE_MENU_SECURITY` | Device menu entry + Security menu title |
| `MENU_ENABLE_DISABLE_INTERFACES` | `DEVICE_MENU_INTERFACES` | Device menu entry + Interfaces menu title |
| `MENU_MANAGE_STORAGE` | `MAIN_MENU_MANAGE_STORAGE`, `STORAGE_MENU_TITLE`, `STORAGE_MENU_HEADER` | Main menu entry + Storage menu title/header |

**Translation Count Reduction**: 10 merged keys replaced 14 original keys = **4 fewer translations per language**

## Hardware Device Name Mergers (HARDWARE_* prefix)

These keys consolidate hardware/storage device names used across multiple contexts:

| Merged Key | Old Keys | Usage Count | Contexts |
|-----------|----------|-------------|----------|
| `HARDWARE_SMARTCARD` | `ADD_WALLET_SMARTCARD`, `SEEDPHRASE_MENU_TO_SMARTCARD`, `SEEDPHRASE_MENU_FROM_SMARTCARD`, `INTERFACES_MENU_SMARTCARD` | 4 | Add wallet, Store seedphrase, Clear seedphrase, Enable/disable interface |
| `HARDWARE_SD_CARD` | `ADD_WALLET_SD_CARD`, `SEEDPHRASE_MENU_TO_SD`, `SEEDPHRASE_MENU_FROM_SD`, `FIRMWARE_MENU_SD_CARD`, `INTERFACES_MENU_SD_CARD` | 5 | Add wallet, Store seedphrase, Clear seedphrase, Firmware update, Enable/disable interface |
| `HARDWARE_INTERNAL_FLASH` | `ADD_WALLET_INTERNAL_FLASH`, `SEEDPHRASE_MENU_TO_FLASH`, `SEEDPHRASE_MENU_FROM_FLASH` | 3 | Add wallet, Store seedphrase, Clear seedphrase |
| `HARDWARE_USB` | `FIRMWARE_MENU_USB`, `INTERFACES_MENU_USB` | 2 | Firmware update, Enable/disable interface |
| `HARDWARE_QR_CODE` | `ADD_WALLET_QR_CODE`, `FIRMWARE_MENU_QR` | 2 | Add wallet, Firmware update |

**Translation Count Reduction**: 5 merged keys replaced 16 original keys = **11 fewer translations per language**

## Common Terms (COMMON_* prefix)

Already existing keys consistently used across the codebase:

| Key | Usage |
|-----|-------|
| `COMMON_SINGLESIG` | SingleSig wallet type |
| `COMMON_MULTISIG` | MultiSig wallet type |
| `COMMON_MAINNET` | Bitcoin mainnet |
| `COMMON_TESTNET` | Bitcoin testnet |

Previously: `GENERATE_SEED_SINGLESIG`, `GENERATE_SEED_MULTISIG`, `GENERATE_SEED_MAINNET`, `GENERATE_SEED_TESTNET` were consolidated to use these common keys.

**Translation Count Reduction**: 4 consolidated uses of existing keys = **4 fewer translations per language**

## Total Impact

**Before**: ~145 translation keys
**After**: ~130 translation keys (15 keys merged)

**Workload Reduction**: ~10% fewer translations required per new language
**Consistency Benefit**: Hardware names and menu titles guaranteed to match across all contexts

## Files Updated

### Translation Files
- `scenarios/MockUI/i18n/specter_ui_en.json` - Added merged keys
- `scenarios/MockUI/i18n/specter_ui_de.json` - Added German translations for merged keys

### Python Files Updated
- `scenarios/MockUI/basic/main_menu.py`
- `scenarios/MockUI/wallet/wallet_menu.py`
- `scenarios/MockUI/wallet/change_wallet_menu.py`
- `scenarios/MockUI/wallet/add_wallet_menu.py`
- `scenarios/MockUI/wallet/seedphrase_menu.py`
- `scenarios/MockUI/wallet/generate_seedphrase_menu.py`
- `scenarios/MockUI/device/device_menu.py`
- `scenarios/MockUI/device/storage_menu.py`
- `scenarios/MockUI/device/firmware_menu.py`
- `scenarios/MockUI/device/interfaces_menu.py`

## Migration Notes

The old keys have been completely replaced in the codebase. Future language files should only include the new merged keys. The old keys can be considered deprecated and should not be used in new code.
