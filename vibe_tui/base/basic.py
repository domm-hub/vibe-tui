import re
from wcwidth import wcswidth, wcwidth
from .theme import Theme
from term_image.image import BlockImage
from PIL import Image
import os

# Robust ANSI regex covering CSI, OSC, and other common sequences
ANSI_REGEX = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*[\x07\x1b\\])')

def strip_ansi(text):
    return ANSI_REGEX.sub('', text)

def real_len(text):
    """Uses wcswidth to get the true visual column width of a string."""
    # Safety: ensure we are stripping all types of escape sequences
    clean = strip_ansi(text)
    return wcswidth(clean)

def truncate_ansi(text, max_len):
    """Truncates a string containing ANSI codes to a specific visual length."""
    if max_len <= 0:
        return ""
    current_visual_len = 0
    res = ""
    # Use the robust regex for splitting
    parts = ANSI_REGEX.split(text)
    
    # We need to find the matches to re-insert them
    matches = ANSI_REGEX.findall(text)
    
    # Re-stitching while truncating
    for i, part in enumerate(parts):
        # Add the text part
        for char in part:
            w = max(0, wcwidth(char))
            if current_visual_len + w <= max_len:
                res += char
                current_visual_len += w
            else:
                return res # Done
        
        # Add the ANSI part if it exists
        if i < len(matches):
            res += matches[i]
            
    return res

def wrap(text, w, h, chars=Theme.borders, color=None, title="", title_pos="left", mode="wrap"):
    # 1. Determine actual border widths and presence
    v_left = chars.get('v', '')
    v_right = v_left # Assume symmetry for basic wrap
    l_w = real_len(v_left)
    r_w = real_len(v_right)
    
    # Check if we should even render top/bottom borders
    has_top = any(chars.get(k) for k in ['tl', 'tr', 'h']) or title
    has_bottom = any(chars.get(k) for k in ['bl', 'br', 'h'])
    
    t_h = 1 if has_top else 0
    b_h = 1 if has_bottom else 0

    inner_w = max(0, w - l_w - r_w)
    inner_h = max(0, h - t_h - b_h)
    
    raw_lines = text.splitlines()
    final_lines = []
    
    for line in raw_lines:
        if not line:
            final_lines.append(" " * inner_w)
            continue
            
        if mode == "truncate":
            clean_line = truncate_ansi(line, inner_w)
            padding = " " * (inner_w - real_len(clean_line))
            final_lines.append(clean_line + padding)
            continue

        current_line = ""
        current_visual_len = 0
        
        # Using the robust regex to split line into text and escape sequences
        parts = ANSI_REGEX.split(line)
        matches = ANSI_REGEX.findall(line)
        
        for i, part in enumerate(parts):
            # Process text part
            for char in part:
                char_w = max(0, wcwidth(char))
                if current_visual_len + char_w <= inner_w:
                    current_line += char
                    current_visual_len += char_w
                else:
                    padding = " " * (inner_w - current_visual_len)
                    final_lines.append(current_line + padding)
                    current_line = char
                    current_visual_len = char_w
            
            # Process ANSI part
            if i < len(matches):
                current_line += matches[i]
                        
        if current_line:
            padding = " " * (inner_w - current_visual_len)
            final_lines.append(current_line + padding)

    # Box Construction
    res = []
    reset = "\x1b[0m"
    style = color if color else ""
    
    # Title/Top Border
    if has_top:
        tl = chars.get('tl', '')
        tr = chars.get('tr', '')
        h_char = chars.get('h', ' ')
        
        if title:
            t_str = f"| {title} |"
            t_len = real_len(t_str)
            if title_pos == "right":
                top_bar = f"{h_char * max(0, inner_w - t_len)}{t_str}"
            elif title_pos == "center":
                left = max(0, (inner_w - t_len) // 2)
                right = max(0, inner_w - t_len - left)
                top_bar = f"{h_char * left}{t_str}{h_char * right}"
            else:
                top_bar = f"{t_str}{h_char * max(0, inner_w - t_len)}"
            res.append(f"{style}{tl}{top_bar}{tr}{reset}")
        else:
            res.append(f"{style}{tl}{h_char * inner_w}{tr}{reset}")

    # Body Construction
    for i in range(inner_h):
        line = final_lines[i] if i < len(final_lines) else " " * inner_w
        res.append(f"{style}{v_left}{reset}{line}{style}{v_right}{reset}")
        
    # Bottom Border
    if has_bottom:
        bl = chars.get('bl', '')
        br = chars.get('br', '')
        h_char = chars.get('h', ' ')
        res.append(f"{style}{bl}{h_char * inner_w}{br}{reset}")
        
    return res[:h]

def get_image_box(image_path, w, h, chars=Theme.NONE, color="\x1b[32m"):
    """
    Creates a UI box with an image 'stamped' inside using relative positioning.
    """
    # 1. Determine actual border widths and presence
    v_left = chars.get('v', '')
    v_right = v_left # Assume symmetry
    l_w = real_len(v_left)
    r_w = real_len(v_right)
    
    # Check for top/bottom presence
    has_top = any(chars.get(k) for k in ['tl', 'tr', 'h'])
    has_bottom = any(chars.get(k) for k in ['bl', 'br', 'h'])
    
    t_h = 1 if has_top else 0
    b_h = 1 if has_bottom else 0

    inner_w = max(0, w - l_w - r_w)
    inner_h = max(0, h - t_h - b_h)
    reset = "\x1b[0m"
    style = color if color else ""
    
    empty_block = [f"{style}{v_left}{reset}{' ' * inner_w}{style}{v_right}{reset}" for _ in range(inner_h)]
    if has_top:
        tl, tr, h_char = chars.get('tl', ''), chars.get('tr', ''), chars.get('h', ' ')
        empty_block.insert(0, f"{style}{tl}{h_char * inner_w}{tr}{reset}")
    if has_bottom:
        bl, br, h_char = chars.get('bl', ''), chars.get('br', ''), chars.get('h', ' ')
        empty_block.append(f"{style}{bl}{h_char * inner_w}{br}{reset}")

    if not os.path.exists(image_path):
        return empty_block[:h]

    # 1. Generate Image Lines
    try:
        with Image.open(image_path) as pil_img:
            img = BlockImage(pil_img)
            img.set_size(frame_size=(inner_w, inner_h))
            img_lines = str(img).splitlines()
    except Exception:
        return empty_block[:h]

    res = []
    
    # 2. Top Border
    if has_top:
        tl = chars.get('tl', '')
        tr = chars.get('tr', '')
        h_char = chars.get('h', ' ')
        res.append(f"{style}{tl}{h_char * inner_w}{tr}{reset}")

    # 3. Calculate Vertical Centering
    img_height = len(img_lines)
    vert_pad_top = max(0, (inner_h - img_height) // 2)

    # 4. Body Construction
    for i in range(inner_h):
        if i < vert_pad_top:
            body_line = " " * inner_w
        elif i < vert_pad_top + img_height:
            img_index = i - vert_pad_top
            raw_line = img_lines[img_index]
            line_vis_w = real_len(raw_line)
            if line_vis_w > inner_w:
                 raw_line = truncate_ansi(raw_line, inner_w)
            elif line_vis_w < inner_w:
                 raw_line += " " * (inner_w - line_vis_w)
                 
            body_line = f"{raw_line}{reset}"
        else:
            body_line = " " * inner_w
            
        res.append(f"{style}{v_left}{reset}{body_line}{style}{v_right}{reset}")

    # 5. Bottom Border
    if has_bottom:
        bl = chars.get('bl', '')
        br = chars.get('br', '')
        h_char = chars.get('h', ' ')
        res.append(f"{style}{bl}{h_char * inner_w}{br}{reset}")
    
    return res[:h]