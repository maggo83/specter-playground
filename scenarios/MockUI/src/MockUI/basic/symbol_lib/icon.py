"""Core Icon class and bitmap conversion utilities."""

import lvgl as lv
from ..ui_consts import WHITE_HEX


def color_to_rgb(color):
    """
    Extract RGB values from an LVGL color object.
    
    Args:
        color: lv.color_t object (e.g., from lv.color_hex(0xFF0000)) or integer
    
    Returns:
        tuple: (r, g, b) values as integers (0-255)
    """
    try:
        # Try to get RGB values from color object methods/attributes
        r = color.red() if callable(getattr(color, 'red', None)) else color.red
        g = color.green() if callable(getattr(color, 'green', None)) else color.green
        b = color.blue() if callable(getattr(color, 'blue', None)) else color.blue
    except (AttributeError, TypeError):
        # Fallback: if it's already an integer, extract RGB
        color_int = int(color)
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
    
    return (r, g, b)


def create_icon_from_bitmap(pattern, width, height, color):
    """
    Convert an alpha-channel bitmap pattern to ARGB8888 format for LVGL.
    
    Args:
        pattern: bytes or list of alpha values (0-255) for each pixel, or
                 list of 0s and 1s for legacy binary patterns
        width: Width of the icon in pixels
        height: Height of the icon in pixels
        color: lv.color_t object (e.g., from lv.color_hex(0xFF0000))
    
    Returns:
        lv.image_dsc_t object ready to use with lv.image
    """
    # Extract RGB components from color
    r, g, b = color_to_rgb(color)
    
    # Detect if pattern is legacy binary (only 0 and 1) or 8-bit alpha (0-255)
    # Check the maximum value to determine format
    max_value = max(pattern) if pattern else 0
    is_binary = max_value <= 1
    
    icon_data_argb = []
    for alpha in pattern:
        # Handle both 8-bit alpha (0-255) and legacy binary (0/1) patterns
        if is_binary:
            # Legacy binary format: 0=transparent, 1=fully opaque
            alpha_value = 0xFF if alpha == 1 else 0x00
        else:
            # 8-bit alpha value (0-255)
            alpha_value = int(alpha)
        
        # Apply user's color with the alpha from the pattern (BGRA byte order for ARGB8888)
        icon_data_argb.extend([b, g, r, alpha_value])
    
    icon_data_bytes = bytes(icon_data_argb)
    
    # Create LVGL image descriptor
    return lv.image_dsc_t({
        'header': {
            'w': width,
            'h': height,
            'cf': lv.COLOR_FORMAT.ARGB8888,
        },
        'data_size': len(icon_data_bytes),
        'data': icon_data_bytes,
    })


class Icon:
    """
    Reusable icon class that can be rendered as an image.
    
    Can be called with a color to create a new Icon with that color:
        icon = BTC_ICONS.CHECKMARK(GREEN_HEX)
    
    Or used directly (will use white as default color):
        icon = BTC_ICONS.CHECKMARK
    
    NOTE: Unlike lv.SYMBOL.*, custom bitmap icons cannot be directly concatenated 
    into strings because they're images, not font characters. Use create_image() 
    to add icons to buttons/containers with flex layout alongside labels.
    """
    
    # Class-level cache shared across all Icon instances
    # Key: (pattern_id, color_string) -> Value: lv.image_dsc_t
    _global_image_dsc_cache = {}
    
    def __init__(self, pattern, width, height, color=None):
        """
        Initialize an icon with a bitmap pattern.
        
        Args:
            pattern: bytes or list of alpha values (0-255) for each pixel,
                    or list of 0s and 1s for legacy binary patterns
            width: Width of the icon in pixels
            height: Height of the icon in pixels
            color: Optional lv.color_t object (defaults to WHITE_HEX)
        """
        self.pattern = pattern
        self.width = width
        self.height = height
        self.color = color if color is not None else WHITE_HEX
    
    def __call__(self, color):
        """
        Create a new Icon instance with the specified color.
        Reuses the same pattern data.
        
        Args:
            color: lv.color_t object (e.g., from lv.color_hex(0xFF0000))
        
        Returns:
            New Icon instance with the specified color
        """
        return Icon(self.pattern, self.width, self.height, color)
    
    def get_image_dsc(self):
        """
        Get an lv.image_dsc_t for this icon.
        Results are cached in the global cache to avoid recreating descriptors.
        
        Returns:
            lv.image_dsc_t object
        """
        # Extract RGB values from color object to create unique cache key
        r, g, b = color_to_rgb(self.color)
        
        # Use pattern identity and RGB values as cache key
        cache_key = (id(self.pattern), r, g, b)
        
        if cache_key not in Icon._global_image_dsc_cache:
            Icon._global_image_dsc_cache[cache_key] = create_icon_from_bitmap(
                self.pattern, self.width, self.height, self.color
            )
        
        return Icon._global_image_dsc_cache[cache_key]
    
    def add_to_parent(self, parent):
        """
        Add this icon to a parent lv.image object.
        Uses the icon's stored color.
        
        Args:
            parent: The lv.image object to configure
        """
        parent.set_src(self.get_image_dsc())
        parent.set_size(self.width, self.height)
