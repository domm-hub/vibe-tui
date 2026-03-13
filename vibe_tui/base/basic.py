import re

# Standard ANSI regex to find CSI (Control Sequence Introducer) codes
ANSI_REGEX = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')

def strip_ansi(text):
    """Removes ANSI escape codes so we can measure the real visible width."""
    return ANSI_REGEX.sub('', text)

def real_len(text):
    """Accurately calculates the visual width of a string containing ANSI codes."""
    return len(strip_ansi(text))

def display(x):
    return "\n".join(x)

import re

def wrap(text, w, h, chars=None, color=None, title="", title_pos="left"):
    if chars is None:
        chars = {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"}
    
    inner_w = max(0, w - 2)
    inner_h = max(0, h - 2)
    
    # 1. Wrapping Logic
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
                    if current_visual_len < inner_w:
                        current_line += char
                        current_visual_len += 1
                    else:
                        wrapped_lines.append(current_line)
                        current_line = char
                        current_visual_len = 1
        if current_line: wrapped_lines.append(current_line)

    # 2. Box Construction
    res = []
    reset = "\x1b[0m"
    style = color if color else ""
    
    # Title Logic
    if title:
        t_str = f"| {title} |"
        if title_pos == "right":
            # Padding to the left, title to the right
            pad_len = max(0, inner_w - len(t_str))
            top_bar = f"{chars['h'] * pad_len}{t_str}"
        elif title_pos == "center":
            left = (inner_w - len(t_str)) // 2
            right = inner_w - len(t_str) - left
            top_bar = f"{chars['h'] * left}{t_str}{chars['h'] * right}"
        else: # Default left
            top_bar = f"{t_str}{chars['h'] * max(0, inner_w - len(t_str))}"
            
        res.append(f"{style}{chars['tl']}{top_bar}{chars['tr']}{reset}")
    else:
        res.append(f"{style}{chars['tl']}{chars['h'] * inner_w}{chars['tr']}{reset}")
    
    # 3. Body Construction
    for i in range(inner_h):
        line = wrapped_lines[i] if i < len(wrapped_lines) else ""
        v_len = len(re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', line))
        padding = " " * (inner_w - v_len)
        res.append(f"{style}{chars['v']}{reset}{line}{padding}{style}{chars['v']}{reset}")
        
    res.append(f"{style}{chars['bl']}{chars['h'] * inner_w}{chars['br']}{reset}")
    return res[:h]