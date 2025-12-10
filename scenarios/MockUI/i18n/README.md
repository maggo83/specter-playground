# Internationalization (i18n) System for Specter UI

This directory contains the internationalization framework for the Specter UI, enabling multi-language support.

## Overview

The i18n system provides:
- Multi-language support with JSON-based translation files
- Automatic fallback to default language (English) for missing translations
- Persistent language selection across sessions
- Easy integration with UI components
- Language file validation (2-letter ISO 639-1 codes only)

## File Structure

```
i18n/
├── __init__.py              # Module exports
├── i18n_manager.py          # Core i18n management class
├── specter_ui_en.json       # English translations (default/reference)
├── specter_ui_de.json       # German translations
└── language_config.json     # User's selected language (auto-generated)
```

Language files must follow naming convention: `specter_ui_XX.json` where XX is a 2-letter ISO 639-1 language code (lowercase). Files with invalid codes (not exactly 2 letters or containing non-alphabetic characters) will be ignored with a warning.

## Language File Format

### English (Reference Language)
```json
{
  "_metadata": {
    "language_code": "en",
    "language_name": "English",
    "version": "1.0"
  },
  "translations": {
    "KEY_NAME": "Translated text"
  }
}
```

### Other Languages
```json
{
  "_metadata": {
    "language_code": "de",
    "language_name": "Deutsch",
    "version": "1.0"
  },
  "translations": {
    "KEY_NAME": {
      "text": "Übersetzer Text",
      "ref_en": "Translated text"
    }
  }
}
```

The `ref_en` field provides English reference text for translators, making it easy to see the original text without scrolling.

## Usage in UI Code

### Initialize in NavigationController
The i18n manager is automatically initialized in the NavigationController:

```python
from ..i18n import I18nManager

class NavigationController(lv.obj):
    def __init__(self, specter_state=None, ui_state=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.i18n = I18nManager()
```

### Use in Menu Classes

```python
def MyMenu(parent, *args, **kwargs):
    # Get translation function from i18n manager (always available via NavigationController)
    t = parent.i18n.t
    
    # Use t() function to translate strings
    menu_items = [
        (icon, t("MENU_ITEM_KEY"), "action", None),
        (None, t("SECTION_HEADER"), None, None),
    ]
    
    return GenericMenu("menu_id", t("MENU_TITLE"), menu_items, parent, *args, **kwargs)
```

**Note**: The i18n manager is always available through `parent.i18n` since it's initialized in the NavigationController. There's no need to check for its existence or use fallback imports.

### Translation Key Naming Convention

Keys follow the pattern: `CATEGORY_SUBCATEGORY_ITEM`

Examples:
- `MAIN_MENU_TITLE` - Main menu title
- `WALLET_MENU_VIEW_ADDRESSES` - Wallet menu item
- `BUTTON_BACK` - Generic back button
- `COMMON_WALLET` - Common term used in multiple places

## Adding a New Language

1. Create a new language file: `specter_ui_XX.json` (where XX is the ISO 639-1 language code)
2. Copy the structure from `specter_ui_de.json`
3. Translate all `text` fields, keeping `ref_en` as English reference
4. Set correct `language_code` and `language_name` in metadata

Example for French:
```json
{
  "_metadata": {
    "language_code": "fr",
    "language_name": "Français",
    "version": "1.0"
  },
  "translations": {
    "MAIN_MENU_TITLE": {
      "text": "Que voulez-vous faire?",
      "ref_en": "What do you want to do?"
    }
  }
}
```

4. The new language will be automatically detected on next startup

## Adding New Translatable Text

1. Choose an appropriate key name following the naming convention
2. Add the English text to `specter_ui_en.json`:
   ```json
   "NEW_KEY_NAME": "English text"
   ```
3. Add translations to all other language files:
   ```json
   "NEW_KEY_NAME": {
     "text": "Translated text",
     "ref_en": "English text"
   }
   ```
4. Use `t("NEW_KEY_NAME")` in your code

## API Reference

### I18nManager Class

#### Methods

- `__init__(i18n_dir=None)` - Initialize manager, load language files
- `set_language(lang_code)` - Switch to a different language
- `get_language()` - Get current language code
- `get_available_languages()` - List available language codes
- `get_language_name(lang_code)` - Get human-readable language name
- `t(key)` - Get translation for a key

#### Global Functions

- `get_i18n_manager()` - Get or create global i18n manager instance
- `t(key)` - Convenience function using global manager

## Language Selection

The last selected language is automatically saved to `language_config.json` and restored on next startup. If no language has been selected, English is used as the default.

## Missing Translations

When a translation key is missing in a language file:
1. A warning is issued during language file load (showing the count of missing keys)
2. The default language (English) translation is used as fallback
3. The missing key is automatically filled from the default language during load
4. The UI continues to work normally

Warnings are issued per language file load, so you'll see them each time a language is selected if keys are missing.

## Technical Details

- **File Format**: JSON for human readability and easy editing
- **Encoding**: UTF-8 to support all languages
- **Language Codes**: ISO 639-1 (2-letter alphabetic codes: en, de, fr, es, etc.)
- **Code Validation**: Language codes must be exactly 2 letters (a-z or A-Z), stored as lowercase
- **Fallback**: Default language (English) is always loaded as reference
- **Performance**: Translations loaded once at startup, no runtime overhead
- **Memory**: All translations kept in memory for fast access
- **Initialization**: I18nManager is created by NavigationController and passed to all child menus

## Status Bar Language Indicator

The current language is displayed in the status bar as a 2-3 letter code (e.g., "EN", "DE", "FR"). The indicator is visible even when the device is locked.

## Future Enhancements

Possible future improvements:
- UI menu for changing language (currently requires editing config file)
- Language-specific formatting (dates, numbers, currencies)
- Right-to-left (RTL) language support
- Plural forms handling
- Context-specific translations
- Translation validation tools

## Contributing Translations

To contribute a new language translation:
1. Fork the repository
2. Create a new language file following the format above
3. Translate all strings
4. Test the translations in the UI
5. Submit a pull request

Please ensure:
- All keys from English file are present
- Translations are accurate and natural
- Special characters are properly escaped
- Metadata is correctly filled

---

For questions or issues, please open an issue on the repository.
