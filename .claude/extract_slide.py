#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from datetime import datetime
import json

# Constants
SLIDE_WIDTH_EMU = 12192000   # 16:9
SLIDE_HEIGHT_EMU = 6858000
EMU_PER_INCH = 914400
PX_PER_INCH = 96

# Parse slide XML
slide_xml = r'C:\project\docs\workspace\brandnew-unpacked\ppt\slides\slide1.xml'
tree = ET.parse(slide_xml)
root = tree.getroot()

# Define namespaces
ns = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}

# Conversion functions
def emu_to_percent(value, slide_dimension):
    """Convert EMU to percentage of slide dimension"""
    return (value / slide_dimension) * 100

def emu_to_px(value):
    """Convert EMU to pixels"""
    return value / EMU_PER_INCH * PX_PER_INCH

# Analyze picture (full slide background)
pictures = root.findall('.//p:pic', ns)
pic_info = {}
if pictures:
    pic = pictures[0]
    sp_pr = pic.find('.//p:spPr', ns)
    xfrm = sp_pr.find('.//a:xfrm', ns) if sp_pr is not None else None
    if xfrm is not None:
        off = xfrm.find('a:off', ns)
        ext = xfrm.find('a:ext', ns)
        x = int(off.get('x')) if off is not None else 0
        y = int(off.get('y')) if off is not None else 0
        cx = int(ext.get('cx')) if ext is not None else 0
        cy = int(ext.get('cy')) if ext is not None else 0

        pic_info = {
            'id': 'shape-0',
            'name': 'Background Photo',
            'type': 'picture',
            'z_index': 0,
            'geometry': {
                'x': f"{emu_to_percent(x, SLIDE_WIDTH_EMU):.1f}%",
                'y': f"{emu_to_percent(y, SLIDE_HEIGHT_EMU):.1f}%",
                'cx': f"{emu_to_percent(cx, SLIDE_WIDTH_EMU):.1f}%",
                'cy': f"{emu_to_percent(cy, SLIDE_HEIGHT_EMU):.1f}%",
                'rotation': 0,
                'original_aspect_ratio': round(emu_to_px(cx) / emu_to_px(cy), 3)
            },
            'style': {
                'fill': {
                    'type': 'image',
                    'opacity': 1.0
                },
                'stroke': {
                    'color': 'none',
                    'width': 0
                },
                'shadow': {
                    'enabled': False
                },
                'rounded_corners': 0
            },
            'text': {
                'has_text': False
            }
        }

# Extract text shapes
shapes = root.findall('.//p:sp', ns)
text_shapes = []
z_index = 1

for shape in shapes:
    nv_sp_pr = shape.find('.//p:nvSpPr', ns)
    sp_pr = shape.find('.//p:spPr', ns)
    tx_body = shape.find('.//p:txBody', ns)

    if nv_sp_pr is not None:
        c_nv_pr = nv_sp_pr.find('.//p:cNvPr', ns)
        if c_nv_pr is not None:
            name = c_nv_pr.get('name')
            shape_id = c_nv_pr.get('id')

            # Get position and size
            xfrm = sp_pr.find('.//a:xfrm', ns) if sp_pr is not None else None
            if xfrm is not None:
                off = xfrm.find('a:off', ns)
                ext = xfrm.find('a:ext', ns)
                x = int(off.get('x')) if off is not None else 0
                y = int(off.get('y')) if off is not None else 0
                cx = int(ext.get('cx')) if ext is not None else 0
                cy = int(ext.get('cy')) if ext is not None else 0

                # Get fill color
                fill_color = 'none'
                fill_opacity = 1.0
                solid_fill = sp_pr.find('.//a:solidFill', ns) if sp_pr is not None else None
                if solid_fill is not None:
                    no_fill = sp_pr.find('.//a:noFill', ns)
                    if no_fill is None:
                        fill_color = 'light'
                        fill_opacity = 1.0

                # Get stroke
                ln = sp_pr.find('.//a:ln', ns) if sp_pr is not None else None
                stroke_width = 0
                stroke_color = 'none'
                if ln is not None:
                    w = ln.get('w')
                    if w:
                        stroke_width = int(w) // 12700  # EMU to pt
                    solid_fill_ln = ln.find('.//a:solidFill', ns)
                    if solid_fill_ln is not None:
                        stroke_color = 'light'

                # Get text properties
                has_text = tx_body is not None
                text_content = ""
                font_size_pt = 0
                font_weight = "normal"
                alignment = "left"
                font_color = "light"

                if tx_body is not None:
                    paragraphs = tx_body.findall('.//a:p', ns)
                    texts = []
                    for para in paragraphs:
                        # Get alignment
                        p_pr = para.find('.//a:pPr', ns)
                        if p_pr is not None and p_pr.get('algn'):
                            algn = p_pr.get('algn')
                            alignment = 'center' if algn == 'ctr' else 'right' if algn == 'r' else 'left'

                        # Get text and properties
                        text_runs = para.findall('.//a:r', ns)
                        for run in text_runs:
                            t = run.find('.//a:t', ns)
                            if t is not None and t.text:
                                texts.append(t.text)

                            # Get font size from run properties
                            rpr = run.find('.//a:rPr', ns)
                            if rpr is not None:
                                sz = rpr.get('sz')
                                if sz and not font_size_pt:
                                    font_size_pt = int(sz) / 100
                                if rpr.get('b') == '1':
                                    font_weight = "bold"

                                # Get text color
                                color_fill = rpr.find('.//a:solidFill', ns)
                                if color_fill is not None:
                                    scheme_clr = color_fill.find('.//a:schemeClr', ns)
                                    if scheme_clr is not None:
                                        clr_val = scheme_clr.get('val')
                                        if clr_val == 'bg1':
                                            font_color = 'light'
                                        elif clr_val == 'tx1':
                                            font_color = 'dark_text'

                    text_content = "".join(texts)

                # Calculate font size ratio
                font_size_ratio = round(font_size_pt / 1080, 6) if font_size_pt > 0 else 0

                shape_info = {
                    'id': f'shape-{z_index}',
                    'name': name,
                    'type': 'textbox',
                    'z_index': z_index,
                    'geometry': {
                        'x': f"{emu_to_percent(x, SLIDE_WIDTH_EMU):.1f}%",
                        'y': f"{emu_to_percent(y, SLIDE_HEIGHT_EMU):.1f}%",
                        'cx': f"{emu_to_percent(cx, SLIDE_WIDTH_EMU):.1f}%",
                        'cy': f"{emu_to_percent(cy, SLIDE_HEIGHT_EMU):.1f}%",
                        'rotation': 0,
                        'original_aspect_ratio': round(emu_to_px(cx) / emu_to_px(cy), 3) if emu_to_px(cy) > 0 else 1.0
                    },
                    'style': {
                        'fill': {
                            'type': 'solid',
                            'color': 'none' if fill_color == 'none' else fill_color,
                            'opacity': fill_opacity
                        },
                        'stroke': {
                            'color': stroke_color,
                            'width': stroke_width
                        },
                        'shadow': {
                            'enabled': False
                        },
                        'rounded_corners': 0
                    },
                    'text': {
                        'has_text': has_text,
                        'content': text_content if text_content else None,
                        'alignment': alignment,
                        'font_size_ratio': font_size_ratio,
                        'original_font_size_pt': font_size_pt if font_size_pt > 0 else None,
                        'font_weight': font_weight,
                        'font_color': font_color
                    }
                }

                text_shapes.append(shape_info)
                z_index += 1

# Extract connector (line)
connectors = root.findall('.//p:cxnSp', ns)
connector_shapes = []
z_index_conn = z_index

for conn in connectors:
    nv_cxn_sp_pr = conn.find('.//p:nvCxnSpPr', ns)
    sp_pr = conn.find('.//p:spPr', ns)

    if nv_cxn_sp_pr is not None:
        c_nv_pr = nv_cxn_sp_pr.find('.//p:cNvPr', ns)
        if c_nv_pr is not None:
            name = c_nv_pr.get('name')

            xfrm = sp_pr.find('.//a:xfrm', ns) if sp_pr is not None else None
            if xfrm is not None:
                off = xfrm.find('a:off', ns)
                ext = xfrm.find('a:ext', ns)
                x = int(off.get('x')) if off is not None else 0
                y = int(off.get('y')) if off is not None else 0
                cx = int(ext.get('cx')) if ext is not None else 0
                cy = int(ext.get('cy')) if ext is not None else 0

                # Get line properties
                ln = sp_pr.find('.//a:ln', ns) if sp_pr is not None else None
                stroke_width = 16  # Default
                stroke_color = 'light'

                if ln is not None:
                    w = ln.get('w')
                    if w:
                        stroke_width = int(w) // 12700
                    solid_fill = ln.find('.//a:solidFill', ns)
                    if solid_fill is not None:
                        scheme_clr = solid_fill.find('.//a:schemeClr', ns)
                        if scheme_clr is not None and scheme_clr.get('val') == 'bg1':
                            stroke_color = 'light'

                connector_info = {
                    'id': f'shape-{z_index_conn}',
                    'name': name,
                    'type': 'line',
                    'z_index': z_index_conn,
                    'geometry': {
                        'x': f"{emu_to_percent(x, SLIDE_WIDTH_EMU):.1f}%",
                        'y': f"{emu_to_percent(y, SLIDE_HEIGHT_EMU):.1f}%",
                        'cx': f"{emu_to_percent(cx, SLIDE_WIDTH_EMU):.1f}%",
                        'cy': f"{emu_to_percent(cy, SLIDE_HEIGHT_EMU):.1f}%",
                        'rotation': 0,
                        'original_aspect_ratio': 999.9
                    },
                    'style': {
                        'fill': {
                            'type': 'none',
                            'opacity': 0
                        },
                        'stroke': {
                            'color': stroke_color,
                            'width': stroke_width
                        },
                        'shadow': {
                            'enabled': False
                        }
                    },
                    'text': {
                        'has_text': False
                    }
                }
                connector_shapes.append(connector_info)
                z_index_conn += 1

# Combine all shapes
all_shapes = [pic_info] + text_shapes + connector_shapes

print(json.dumps(all_shapes, indent=2, ensure_ascii=False))
