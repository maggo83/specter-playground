"""Optional LVGL renderers for the dependency-free BitSquiggles core.

``render_raster`` preserves the exact binary grid through an integer-scaled
RGB565 image. ``render_smooth`` draws the same selected cells and connections as
an antialiased rounded geometric union on an LVGL canvas.

The module deliberately accepts core outputs rather than fingerprints:

    visual = bitsquiggle32.spec(bits, bitsquiggle32.HIGH_CONTRAST)
    raster = bitsquiggle32.pixels(bits, bitsquiggle32.HIGH_CONTRAST)
    render_raster(parent, raster, scale=2)
    render_smooth(parent, visual, scale=4)

Call ``clear_cache`` after deleting parents that contain raster images or smooth
canvases. The core remains usable without importing LVGL or this module.
"""

import lvgl as lv

import bitsquiggle32

_RASTER_CACHE = {}
_SMOOTH_DRAW_BUFS = []


def _color(hex_value):
    return lv.color_hex(int(hex_value[1:], 16))


def _require_scale(scale):
    if not isinstance(scale, int) or scale < 1:
        raise ValueError("scale must be a positive integer")


def _raster_key(grid, scale):
    return (bytes(grid["pixels"]), grid["background"]["hex"],
            grid["foreground"]["hex"], scale)


def _raster_descriptor(grid, scale):
    key = _raster_key(grid, scale)
    if key in _RASTER_CACHE:
        return _RASTER_CACHE[key]

    width = grid["width"]
    height = grid["height"]
    pixels = grid["pixels"]
    if width != bitsquiggle32.PIXEL_WIDTH or height != bitsquiggle32.PIXEL_HEIGHT:
        raise ValueError("grid must use the canonical BitSquiggles raster dimensions")
    if len(pixels) != width * height:
        raise ValueError("grid has an invalid pixel buffer")

    background = _rgb565_le(grid["background"]["hex"])
    foreground = _rgb565_le(grid["foreground"]["hex"])
    data = bytearray(width * scale * height * scale * 2)
    output_width = width * scale
    for source_y in range(height):
        for source_x in range(width):
            low, high = foreground if pixels[source_y * width + source_x] else background
            for y_offset in range(scale):
                output_y = source_y * scale + y_offset
                for x_offset in range(scale):
                    output_x = source_x * scale + x_offset
                    index = (output_y * output_width + output_x) * 2
                    data[index] = low
                    data[index + 1] = high

    descriptor = lv.image_dsc_t({
        "header": {
            "w": output_width,
            "h": height * scale,
            "cf": lv.COLOR_FORMAT.RGB565,
        },
        "data_size": len(data),
        "data": bytes(data),
    })
    _RASTER_CACHE[key] = descriptor
    return descriptor


def _rgb565_le(hex_value):
    red = int(hex_value[1:3], 16) >> 3
    green = int(hex_value[3:5], 16) >> 2
    blue = int(hex_value[5:7], 16) >> 3
    value = (red << 11) | (green << 5) | blue
    return value & 0xff, value >> 8


def render_raster(parent, grid, scale=1):
    """Return an LVGL image containing an exact integer-scaled raster.

    Every source pixel becomes an exact ``scale`` by ``scale`` RGB565 square;
    no interpolation, antialiasing, or rounding is applied.
    """
    _require_scale(scale)
    image = lv.image(parent)
    image.set_src(_raster_descriptor(grid, scale))
    image.set_size(grid["width"] * scale, grid["height"] * scale)
    return image


def _draw_rect(layer, color, x, y, width, height, radius):
    descriptor = lv.draw_rect_dsc_t()
    descriptor.init()
    descriptor.bg_opa = lv.OPA.COVER
    descriptor.border_opa = lv.OPA.TRANSP
    descriptor.bg_color = color
    descriptor.radius = radius
    area = lv.area_t({
        "x1": x,
        "y1": y,
        "x2": x + width - 1,
        "y2": y + height - 1,
    })
    lv.draw_rect(layer, descriptor, area)


def render_smooth(parent, visual, scale=4, bordered=False):
    """Return a rounded LVGL canvas for a canonical BitSquiggles visual.

    The renderer draws a geometric union of active rounded cells, selected
    bridges, and four-cell junctions. It preserves every selected and
    unselected connection while using LVGL's antialiased shape rasterization.
    """
    _require_scale(scale)
    width = bitsquiggle32.PIXEL_WIDTH * scale
    height = bitsquiggle32.PIXEL_HEIGHT * scale
    foreground = _color(visual["foreground"]["hex"])
    background = _color(visual["background"]["hex"])

    wrapper = lv.obj(parent)
    wrapper.set_size(width, height)
    wrapper.set_style_radius(scale, 0)
    wrapper.set_style_bg_color(background, 0)
    wrapper.set_style_bg_opa(lv.OPA.COVER, 0)
    wrapper.set_style_pad_all(0, 0)
    wrapper.set_style_clip_corner(True, 0)
    wrapper.remove_flag(lv.obj.FLAG.SCROLLABLE)
    if bordered:
        wrapper.set_style_border_color(foreground, 0)
        wrapper.set_style_border_width(1, 0)
        wrapper.set_style_border_opa(lv.OPA.COVER, 0)
    else:
        wrapper.set_style_border_width(0, 0)

    draw_buffer = lv.draw_buf_create(width, height, lv.COLOR_FORMAT.RGB565, 0)
    _SMOOTH_DRAW_BUFS.append(draw_buffer)
    canvas = lv.canvas(wrapper)
    canvas.set_draw_buf(draw_buffer)
    canvas.set_pos(0, 0)
    canvas.fill_bg(background, lv.OPA.COVER)

    layer = lv.layer_t()
    canvas.init_layer(layer)
    cell_size = 2 * scale
    cell_radius = scale
    connections = visual["connections"]
    cells = visual["cells"]

    # Paint one overlapping foreground union. Drawing independent antialiased
    # shapes edge-to-edge leaves background hairlines on LVGL targets, so draw
    # junctions and expanded bridges first, then cover their joins with cells.
    for row in range(bitsquiggle32.ROWS - 1):
        for column in range(bitsquiggle32.COLUMNS - 1):
            if (_connection(connections, row, column, row, column + 1)
                    and _connection(connections, row + 1, column, row + 1, column + 1)
                    and _connection(connections, row, column, row + 1, column)
                    and _connection(connections, row, column + 1, row + 1, column + 1)):
                _draw_rect(layer, foreground, (3 + 3 * column) * scale,
                           (3 + 3 * row) * scale, scale, scale, 0)

    for index, edge in enumerate(bitsquiggle32.EDGES):
        if not connections[index]:
            continue
        start_row, start_column, end_row, end_column = edge
        x = (1 + 3 * start_column) * scale
        y = (1 + 3 * start_row) * scale
        if start_row == end_row:
            _draw_rect(layer, foreground, x + cell_size - cell_radius, y,
                       scale + 2 * cell_radius, cell_size, 0)
        else:
            _draw_rect(layer, foreground, x, y + cell_size - cell_radius,
                       cell_size, scale + 2 * cell_radius, 0)

    for row in range(bitsquiggle32.ROWS):
        for column in range(bitsquiggle32.COLUMNS):
            if cells[row][column]:
                _draw_rect(layer, foreground, (1 + 3 * column) * scale,
                           (1 + 3 * row) * scale, cell_size, cell_size, cell_radius)

    canvas.finish_layer(layer)
    return wrapper


def _connection(connections, start_row, start_column, end_row, end_column):
    for index, edge in enumerate(bitsquiggle32.EDGES):
        if edge == (start_row, start_column, end_row, end_column):
            return connections[index]
    raise ValueError("not a canonical edge")


def clear_cache():
    """Release cached raster descriptors and C-side smooth-canvas buffers."""
    _RASTER_CACHE.clear()
    for draw_buffer in _SMOOTH_DRAW_BUFS:
        try:
            draw_buffer.destroy()
        except Exception:
            pass
    _SMOOTH_DRAW_BUFS.clear()
