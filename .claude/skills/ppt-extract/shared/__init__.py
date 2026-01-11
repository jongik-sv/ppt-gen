"""ppt-extract shared utilities."""

from .ooxml_parser import OOXMLParser, NAMESPACES
from .yaml_utils import save_yaml, load_yaml
from .color_utils import (
    ColorInfo,
    hex_to_rgb,
    rgb_to_hex,
    map_ooxml_colors_to_theme,
    extract_colors_from_image,
    classify_colors_by_role,
    generate_palette_thumbnail
)

__all__ = [
    'OOXMLParser', 'NAMESPACES',
    'save_yaml', 'load_yaml',
    'ColorInfo', 'hex_to_rgb', 'rgb_to_hex',
    'map_ooxml_colors_to_theme', 'extract_colors_from_image',
    'classify_colors_by_role', 'generate_palette_thumbnail'
]
