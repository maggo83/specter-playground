# i18n System Changelog

## Recent Changes (December 10, 2025)

### 1. Language Code Validation
**Issue**: Language files with any filename between prefix and suffix were accepted, potentially allowing invalid codes.

**Solution**: Added strict validation in `_scan_available_languages()`:
- Language codes must be exactly 2 characters long
- Only alphabetic characters (a-z, A-Z) are allowed
- Invalid codes trigger a warning and are ignored
- Codes are normalized to lowercase for consistency

**Example**: `specter_ui_en.json` ✓, `specter_ui_123.json` ✗, `specter_ui_eng.json` ✗

### 2. Consistent Terminology: "Default" vs "English"
**Issue**: Mixed use of "English" and "default" throughout the code was inconsistent.

**Solution**: Standardized terminology:
- All internal references now use "default" instead of "English"
- Variable names: `english_translations` → `default_translations`
- Method names: `_load_english_reference()` → `_load_default_reference()`
- Comments and docstrings updated to refer to "default language"
- `DEFAULT_LANGUAGE = "en"` constant makes it clear that English is the default

This makes it clearer that the fallback mechanism is based on a configurable default, which happens to be English.

### 3. Removed `missing_keys_warned` Variable
**Issue**: The `missing_keys_warned` flag was a class-level variable that needed initialization and resetting.

**Solution**: Simplified the implementation:
- Removed `missing_keys_warned` from `__init__()`
- Removed reset in `set_language()`
- Warning now issued directly at the end of `_load_language_file()` if any keys are missing
- Cleaner logic: check happens once per file load, no state management needed

### 4. Simplified i18n Access in Menu Files
**Issue**: All menu files were checking if i18n exists and falling back to global instance:
```python
i18n = getattr(parent, "i18n", None)
if i18n is None:
    from ..i18n.i18n_manager import get_i18n_manager
    i18n = get_i18n_manager()
t = i18n.t
```

**Solution**: Menus now directly access i18n from parent:
```python
t = parent.i18n.t
```

**Rationale**:
- NavigationController always initializes i18n in `__init__()`
- All menus receive NavigationController as parent
- Checking for existence is unnecessary defensive programming
- Cleaner, more readable code
- Consistent pattern across all files

**Files Updated**:
- `basic/action_screen.py`
- `basic/main_menu.py`
- `basic/locked_menu.py`
- `basic/status_bar.py`
- `wallet/wallet_menu.py`
- `wallet/add_wallet_menu.py`
- `wallet/generate_seedphrase_menu.py`
- `wallet/passphrase_menu.py`
- `wallet/seedphrase_menu.py`
- `device/device_menu.py`
- `device/security_menu.py`
- `device/backups_menu.py`
- `device/firmware_menu.py`
- `device/storage_menu.py`

## Technical Impact

### Performance
No performance impact. Changes are structural improvements without runtime overhead.

### Compatibility
Fully backward compatible:
- Language files format unchanged
- Translation API unchanged (`t(key)` still works the same)
- Existing language preference files still work

### Code Quality
- **Reduced complexity**: Removed unnecessary conditional checks
- **Better maintainability**: Consistent patterns across all files
- **Clearer intent**: Default language concept more explicit
- **Fewer lines of code**: Removed redundant fallback logic

## Migration Guide

If you have custom menu files, update them to use the simplified pattern:

**Before**:
```python
i18n = getattr(parent, "i18n", None)
if i18n is None:
    from ..i18n.i18n_manager import get_i18n_manager
    i18n = get_i18n_manager()
t = i18n.t
```

**After**:
```python
# Get translation function from i18n manager (always available via NavigationController)
t = parent.i18n.t
```

## Validation

All changes validated:
- No syntax errors in modified files
- Only expected MicroPython import warnings (lvgl, urandom, etc.)
- Language code validation tested with edge cases
- Documentation updated to reflect changes
