"""
Example: Integrating German Umlaut Fonts into MockUI

This file demonstrates how to integrate the German umlaut fonts into your MockUI application.
You can use this as a reference or directly import the integration function.
"""

import lvgl as lv
from scenarios.MockUI.fonts import font_loader_de


def integrate_german_fonts():
    """
    Integrate German umlaut fonts into the MockUI.
    
    This function should be called after LVGL is initialized but before creating UI components.
    It loads the German fonts and optionally updates the default theme font.
    
    Returns:
        dict: Dictionary with loaded fonts by size, or None if loading failed
    """
    print("=" * 50)
    print("Integrating German Umlaut Fonts")
    print("=" * 50)
    
    # Font loader already initialized on import, check status
    available_sizes = font_loader_de.get_available_sizes()
    
    if not available_sizes:
        print("ERROR: No German fonts loaded!")
        return None
    
    print(f"✓ Loaded {len(available_sizes)} font sizes: {available_sizes}")
    
    # Get commonly used sizes
    fonts = {
        'status_bar': font_loader_de.get_font(12),  # Used in status bar
        'default': font_loader_de.get_font(16),      # Default UI font
        'large': font_loader_de.get_font(24),        # Large text
    }
    
    # Check if fonts loaded successfully
    for name, font in fonts.items():
        if font:
            print(f"✓ {name} font loaded successfully")
        else:
            print(f"✗ {name} font failed to load")
    
    print("=" * 50)
    return fonts


def apply_font_to_object(obj, size=16):
    """
    Apply a German umlaut font to an LVGL object.
    
    Args:
        obj: LVGL object (label, button, etc.)
        size (int): Font size to apply
    
    Returns:
        bool: True if successful, False otherwise
    """
    font = font_loader_de.get_font(size)
    if font:
        obj.set_style_text_font(font, 0)
        return True
    return False


# Example usage in mock_ui.py:
"""
# Add this near the top of mock_ui.py after imports:
from scenarios.MockUI.fonts.integration_example import integrate_german_fonts, apply_font_to_object

# Add this after LVGL initialization:
fonts = integrate_german_fonts()

# Then when creating UI elements, apply the fonts:
if fonts and fonts['default']:
    # Update theme with German font
    theme = lv.theme_default_init(
        lv.disp_get_default(),
        lv.palette_main(lv.PALETTE.BLUE),
        lv.palette_main(lv.PALETTE.RED),
        True,
        fonts['default']
    )

# Or apply to specific objects:
my_label = lv.label(parent)
my_label.set_text("Test: ÄÖÜ äöü ß")
apply_font_to_object(my_label, 16)
"""
