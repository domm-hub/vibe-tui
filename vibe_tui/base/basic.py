import re
from wcwidth import wcswidth, wcwidth
from .theme import Theme

# Standard ANSI regex
ANSI_REGEX = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')

def strip_ansi(text):
    return ANSI_REGEX.sub('', text)

def real_len(text):
    """Uses wcswidth to get the true visual column width of a string."""
    return wcswidth(strip_ansi(text))

def wrap(text, w, h, chars=None, color=None, title="", title_pos="left"):
    if chars is None:
        chars = Theme.borders
    
    inner_w = max(0, w - 2)
    inner_h = max(0, h - 2)
    
    raw_lines = text.splitlines()
    wrapped_lines = []
    parts_regex = re.compile(r'(\x1b\[[0-?]*[ -/]*[@-~])')
    
    for line in raw_lines:
        current_line = ""
        current_visual_len = 0
        parts = parts_regex.split(line)
        
        for part in parts:
            if not part: continue
            if part.startswith('\x1b'): 
                current_line += part
            else:
                for char in part:
                    # Calculate true width of the character (0, 1, or 2)
                    char_w = max(0, wcwidth(char))
                    
                    if current_visual_len + char_w <= inner_w:
                        current_line += char
                        current_visual_len += char_w
                    else:
                        # If a wide emoji won't fit, pad the current line and start new
                        padding = " " * (inner_w - current_visual_len)
                        wrapped_lines.append(current_line + padding)
                        current_line = char
                        current_visual_len = char_w
                        
        if current_line:
            padding = " " * (inner_w - current_visual_len)
            wrapped_lines.append(current_line + padding)

    # Box Construction
    res = []
    reset = "\x1b[0m"
    style = color if color else ""
    
    # Title Logic (using real_len for title accuracy)
    if title:
        t_str = f"| {title} |"
        t_len = real_len(t_str)
        if title_pos == "right":
            top_bar = f"{chars['h'] * max(0, inner_w - t_len)}{t_str}"
        elif title_pos == "center":
            left = max(0, (inner_w - t_len) // 2)
            right = max(0, inner_w - t_len - left)
            top_bar = f"{chars['h'] * left}{t_str}{chars['h'] * right}"
        else:
            top_bar = f"{t_str}{chars['h'] * max(0, inner_w - t_len)}"
        res.append(f"{style}{chars['tl']}{top_bar}{chars['tr']}{reset}")
    else:
        res.append(f"{style}{chars['tl']}{chars['h'] * inner_w}{chars['tr']}{reset}")
    
    # Body Construction
    for i in range(inner_h):
        line = wrapped_lines[i] if i < len(wrapped_lines) else " " * inner_w
        res.append(f"{style}{chars['v']}{reset}{line}{style}{chars['v']}{reset}")
        
    res.append(f"{style}{chars['bl']}{chars['h'] * inner_w}{chars['br']}{reset}")
    return res[:h]