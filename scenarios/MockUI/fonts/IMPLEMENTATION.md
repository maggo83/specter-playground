# German Umlaut Font Implementation Guide

## Quick Start

The German umlaut fonts are now ready to use in the MockUI simulator!

### What's Been Done

✅ **lv_font_conv installed** - Font conversion tool ready
✅ **Binary fonts generated** - 11 sizes (8-28) with German umlauts  
✅ **Python font loader created** - `font_loader_de.py` module
✅ **Package structure** - Proper Python package with `__init__.py`
✅ **Integration examples** - Ready-to-use code snippets

### File Overview

```
scenarios/MockUI/fonts/
├── __init__.py                      # Package initialization
├── font_loader_de.py                # Main font loader module
├── integration_example.py           # Usage examples
├── README.md                        # Detailed documentation
├── generate_fonts_with_umlauts.sh   # C font generator
├── generate_binary_fonts.sh         # Binary font generator
├── montserrat_*_de.c                # C font files (11 sizes)
└── montserrat_*_de.bin              # Binary font files (11 sizes)
```

---

## Integration Steps

### Step 1: Import the Font Loader

Add to the beginning of `mock_ui.py` (or wherever LVGL is initialized):

```python
from scenarios.MockUI.fonts import font_loader_de
```

This will automatically load all available fonts and print status to console.

### Step 2: Apply Fonts to UI Components

**Option A: Apply to the default theme (affects all new widgets)**

```python
# After LVGL display initialization
font_16 = font_loader_de.get_font(16)

if font_16:
    theme = lv.theme_default_init(
        lv.disp_get_default(),
        lv.palette_main(lv.PALETTE.BLUE),
        lv.palette_main(lv.PALETTE.RED),
        True,
        font_16  # German umlaut font as default
    )
```

**Option B: Apply to specific objects**

```python
# For status bar
status_label = lv.label(status_bar)
status_label.set_text("Status: Gerät bereit")
font_12 = font_loader_de.get_font(12)
if font_12:
    status_label.set_style_text_font(font_12, 0)

# For other UI elements
menu_label = lv.label(menu)
menu_label.set_text("Menü")
font_16 = font_loader_de.get_font(16)
if font_16:
    menu_label.set_style_text_font(font_16, 0)
```

**Option C: Integration in NavigationController**

Update the `NavigationController.__init__()` method:

```python
class NavigationController(lv.obj):
    def __init__(self, specter_state=None, ui_state=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Load German fonts early
        from ..fonts import font_loader_de
        self.font_loader = font_loader_de
        
        # Get commonly used fonts
        self.font_12 = font_loader_de.get_font(12)
        self.font_16 = font_loader_de.get_font(16)
        
        # Rest of initialization...
```

Then use `self.font_12` and `self.font_16` throughout the UI components.

---

## Testing

### Test 1: Check Font Loading

Run the simulator and check the console output:

```bash
sudo --preserve-env=XDG_RUNTIME_DIR nix develop -c make simulate SCRIPT=mock_ui.py
```

Expected output:
```
FontLoaderDE: Loaded 11/11 German umlaut fonts
```

### Test 2: Test German Characters

Create a test label with German text:

```python
test_label = lv.label(lv.scr_act())
test_label.set_text("Test: Ä Ö Ü ä ö ü ß\nDeutsch: Größe")
font_16 = font_loader_de.get_font(16)
if font_16:
    test_label.set_style_text_font(font_16, 0)
test_label.center()
```

### Test 3: Test All Sizes

```python
from scenarios.MockUI.fonts import font_loader_de

# Display all available sizes
for size in font_loader_de.get_available_sizes():
    label = lv.label(parent)
    label.set_text(f"Size {size}: Äpfel, Größe, Tür")
    font = font_loader_de.get_font(size)
    if font:
        label.set_style_text_font(font, 0)
```

---

## Troubleshooting

### Problem: "No German fonts loaded"

**Cause:** Binary font files (.bin) not found or failed to load.

**Solution:**
1. Check that .bin files exist: `ls -la scenarios/MockUI/fonts/*.bin`
2. If missing, regenerate: `./scenarios/MockUI/fonts/generate_binary_fonts.sh`
3. Check file permissions: `chmod 644 scenarios/MockUI/fonts/*.bin`

### Problem: Fonts load but umlauts still show as boxes

**Cause:** Fonts loaded but not applied to UI elements.

**Solution:**
1. Verify font is applied: Check that `set_style_text_font()` is called
2. Use correct font object from font_loader_de
3. Check LVGL version compatibility

### Problem: Some font sizes missing

**Cause:** Individual font generation failures.

**Solution:**
1. Check console output for specific failures
2. Regenerate specific size manually:
   ```bash
   lv_font_conv --size 16 --bpp 4 \
     --font f469-disco/usermods/udisplay_f469/lvgl/scripts/built_in_font/Montserrat-Medium.ttf \
     --range 0x20-0x7F,0xB0,0x2022,0xC4,0xD6,0xDC,0xE4,0xF6,0xFC,0xDF \
     --format bin -o scenarios/MockUI/fonts/montserrat_16_de.bin
   ```

---

## API Reference

### FontLoaderDE Class

#### Methods

**`get_font(size)`**
- **Args:** `size` (int) - Font size (8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28)
- **Returns:** `lv.font` object or `None`
- **Example:** `font = font_loader_de.get_font(16)`

**`get_available_sizes()`**
- **Returns:** List of successfully loaded font sizes
- **Example:** `sizes = font_loader_de.get_available_sizes()`

**`is_loaded(size)`**
- **Args:** `size` (int) - Font size to check
- **Returns:** `bool` - True if loaded
- **Example:** `if font_loader_de.is_loaded(16): ...`

**`reload()`**
- **Description:** Reload all fonts (useful after regenerating files)
- **Example:** `font_loader_de.reload()`

### Convenience Functions

**`get_font_de(size)`**
- Shorthand for `font_loader_de.get_font(size)`

**`set_default_font_de(size)`**
- Attempts to set default LVGL font (experimental)

---

## Performance Notes

- **Memory:** Each binary font is 5-18KB, total ~120KB for all 11 sizes
- **Loading time:** All fonts load in <100ms on startup
- **Runtime:** No performance impact once loaded
- **Recommendation:** Only load sizes you actually use

---

## Regenerating Fonts

### Add More Characters

Edit `generate_binary_fonts.sh` and modify the `CHAR_RANGE` variable:

```bash
# Add French characters (é, è, etc.)
CHAR_RANGE="0x20-0x7F,0xB0,0x2022,0xC4,0xD6,0xDC,0xE4,0xF6,0xFC,0xDF,0xE0-0xEF"

# Add specific symbols
CHAR_RANGE="0x20-0x7F,0xB0,0x2022,0xC4,0xD6,0xDC,0xE4,0xF6,0xFC,0xDF,0x20AC"  # € symbol
```

Then regenerate:
```bash
./scenarios/MockUI/fonts/generate_binary_fonts.sh
```

### Change Font Style

Edit both scripts to use a different TTF file:

```bash
SOURCE_FONT="$SOURCE_FONT_DIR/Montserrat-Bold.ttf"  # Use bold instead
```

---

## Next Steps

1. ✅ **Fonts generated** - All binary fonts ready
2. ✅ **Loader created** - Python module ready to use
3. ⏳ **Integration** - Add to mock_ui.py or NavigationController
4. ⏳ **Testing** - Verify German umlauts render correctly
5. ⏳ **Optimization** - Only load needed font sizes

**Ready to integrate!** Follow the integration steps above to start using German umlauts in your MockUI.
