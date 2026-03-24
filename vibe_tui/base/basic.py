import re
from wcwidth import wcswidth, wcwidth
from .theme import Theme
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

import re
from wcwidth import wcwidth

# The "Main Character" Regex for ANSI escape codes
ANSI_REGEX = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def real_len(text):
    """Calculates visible width, ignoring ANSI and handling wide chars."""
    clean_text = ANSI_REGEX.sub('', text)
    return sum(max(0, wcwidth(c)) for c in clean_text)

def truncate_ansi(text, max_w):
    """Truncates text to a specific visual width while keeping ANSI codes."""
    v_len = 0
    res = ""
    # Split by ANSI to keep them intact
    parts = ANSI_REGEX.split(text)
    matches = ANSI_REGEX.findall(text)
    
    for i, part in enumerate(parts):
        for char in part:
            char_w = max(0, wcwidth(char))
            if v_len + char_w <= max_w:
                res += char
                v_len += char_w
            else:
                return res
        if i < len(matches):
            res += matches[i]
    return res

def wrap(text, w, h, chars=None, color=None, title="", title_pos="left", mode="wrap"):
    if chars is None:
        chars = {'v': '│', 'h': '─', 'tl': '╭', 'tr': '╮', 'bl': '╰', 'br': '╯'}
        
    v_left = chars.get('v', '')
    v_right = v_left 
    l_w = real_len(v_left)
    r_w = real_len(v_right)
    
    has_top = any(chars.get(k) for k in ['tl', 'tr', 'h']) or title
    has_bottom = any(chars.get(k) for k in ['bl', 'br', 'h'])
    
    t_h = 1 if has_top else 0
    b_h = 1 if has_bottom else 0

    inner_w = max(0, w - l_w - r_w)
    inner_h = max(0, h - t_h - b_h)
    
    raw_lines = text.splitlines()
    final_lines = []
    active_style = "" # 🚀 THE SECRET SAUCE: Tracks current color state

    for line in raw_lines:
        if not line:
            final_lines.append(" " * inner_w)
            continue
            
        if mode == "truncate":
            clean_line = truncate_ansi(line, inner_w)
            padding = " " * (inner_w - real_len(clean_line))
            final_lines.append(active_style + clean_line + padding)
            continue

        current_line = active_style # Start with the last known style
        current_visual_len = 0
        
        # Split line into text chunks and ANSI matches
        parts = ANSI_REGEX.split(line)
        matches = ANSI_REGEX.findall(line)
        
        for i, part in enumerate(parts):
            for char in part:
                char_w = max(0, wcwidth(char))
                if current_visual_len + char_w <= inner_w:
                    current_line += char
                    current_visual_len += char_w
                else:
                    # WRAP TIME: Close the current line and start a new one with the style
                    padding = " " * (inner_w - current_visual_len)
                    final_lines.append(current_line + "\x1b[0m" + padding)
                    current_line = active_style + char 
                    current_visual_len = char_w
            
            # Update the active style when we hit an ANSI match
            if i < len(matches):
                active_style += matches[i]
                current_line += matches[i]
                        
        if current_line:
            padding = " " * (inner_w - current_visual_len)
            final_lines.append(current_line + "\x1b[0m" + padding)

    # --- Box Construction ---
    res = []
    reset = "\x1b[0m"
    style = color if color else ""
    
    # Top Border & Title
    if has_top:
        tl, tr, h_char = chars.get('tl', ''), chars.get('tr', ''), chars.get('h', ' ')
        if title:
            t_str = f"┤ {title} ├" # Styled title
            t_len = real_len(t_str)
            if title_pos == "right":
                top_bar = f"{h_char * (inner_w - t_len)}{t_str}"
            elif title_pos == "center":
                pad = (inner_w - t_len) // 2
                top_bar = f"{h_char * pad}{t_str}{h_char * (inner_w - t_len - pad)}"
            else:
                top_bar = f"{t_str}{h_char * (inner_w - t_len)}"
            res.append(f"{style}{tl}{top_bar}{tr}{reset}")
        else:
            res.append(f"{style}{tl}{h_char * inner_w}{tr}{reset}")

    # Body Sections
    for i in range(inner_h):
        line = final_lines[i] if i < len(final_lines) else " " * inner_w
        res.append(f"{style}{v_left}{reset}{line}{style}{v_right}{reset}")
        
    # Bottom Border
    if has_bottom:
        bl, br, h_char = chars.get('bl', ''), chars.get('br', ''), chars.get('h', ' ')
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
        from term_image.image import BlockImage
        from PIL import Image
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

#