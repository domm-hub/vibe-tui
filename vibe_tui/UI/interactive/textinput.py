from ...base.theme import Theme
from ...base import wrap
from ...base.colors import Colors
from ..base_widgets import UIBox
from ...node import Node
from ...event.eventmanager import Event
import re
from ... import statements


class UIEditor(UIBox):
    def __init__(self, weight, text="", title=" EDITOR "):
        super().__init__(weight=weight, text=text, title=title, focusable=True)
        self.lines = text.splitlines() if text else [""]
        self.cursor_x = 0
        self.cursor_y = 0
        self.scroll_y = 0
        self.blink_counter = 0

    def handle_input(self, key):
        event = Event(key)
        self.blink_counter = 0 # Reset blink on activity
        modified = False
        if event.is_nav:
            if event.is_up:
                if self.cursor_y > 0:
                    self.cursor_y -= 1
                    self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
            
            elif event.is_down:
                if self.cursor_y < len(self.lines) - 1:
                    self.cursor_y += 1
                    self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
            
            elif event.is_left:
                if self.cursor_x > 0:
                    self.cursor_x -= 1
                elif self.cursor_y > 0:
                    self.cursor_y -= 1
                    self.cursor_x = len(self.lines[self.cursor_y])
            
            elif event.is_right:
                if self.cursor_x < len(self.lines[self.cursor_y]):
                    self.cursor_x += 1
                elif self.cursor_y < len(self.lines) - 1:
                    self.cursor_y += 1
                    self.cursor_x = 0

        if event.is_backspace:
            modified = True
            if self.cursor_x > 0:
                line = self.lines[self.cursor_y]
                self.lines[self.cursor_y] = line[:self.cursor_x-1] + line[self.cursor_x:]
                self.cursor_x -= 1
            elif self.cursor_y > 0:
                # Merge current line with the one above
                prev_len = len(self.lines[self.cursor_y-1])
                self.lines[self.cursor_y-1] += self.lines.pop(self.cursor_y)
                self.cursor_y -= 1
                self.cursor_x = prev_len

        elif event.is_enter:
            modified = True
            # Split line at cursor
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x]
            self.lines.insert(self.cursor_y + 1, line[self.cursor_x:])
            self.cursor_y += 1
            self.cursor_x = 0

        elif event.is_char:
            modified = True
            # Standard character insertion
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x] + event.char + line[self.cursor_x:]
            self.cursor_x += 1
        
        if modified:
            self.emit("change", self.lines)

    def display(self, width, height):
        self.blink_counter += 1
        inner_h = height - 2
        
        # Simple scrolling logic
        if self.cursor_y < self.scroll_y:
            self.scroll_y = self.cursor_y
        elif self.cursor_y >= self.scroll_y + inner_h:
            self.scroll_y = self.cursor_y - inner_h + 1

        # Visible lines
        visible = self.lines[self.scroll_y : self.scroll_y + inner_h]
        
        # Prepare content with cursor
        output_lines = []
        cursor_char = "_" if (self.blink_counter // 15) % 2 == 0 else " "
        
        for i, line in enumerate(visible):
            absolute_y = self.scroll_y + i
            if absolute_y == self.cursor_y and self.selected:
                # Insert cursor into the string for visual feedback
                line_with_cursor = (line[:self.cursor_x] + 
                                   f"{Colors.REVERSE}{cursor_char}{Colors.RESET}" + 
                                   line[self.cursor_x+1:])
                output_lines.append(line_with_cursor)
            else:
                output_lines.append(line)

        self.text = "\n".join(output_lines)
        return super().display(width, height)
    
    def set(self, text):
        self.lines = text.splitlines() if text else [""]
        self.cursor_x = 0
        self.cursor_y = 0
        self.scroll_y = 0

    def set_cursor_pos(self, local_x, local_y):
        inner_x = max(0, local_x - 1)
        inner_y = max(0, local_y - 1)
        target_y = self.scroll_y + inner_y
        
        if target_y < len(self.lines):
            self.cursor_y = target_y
            self.cursor_x = min(inner_x, len(self.lines[self.cursor_y]))
        else:
            self.cursor_y = max(0, len(self.lines) - 1)
            self.cursor_x = len(self.lines[self.cursor_y])


class PythonCode(UIBox):
    def __init__(self, weight, text="", title=" CODE "):
        super().__init__(weight=weight, text=text, title=title, focusable=True)
        self.lines = text.splitlines() if text else [""]
        self.cursor_x = 0
        self.cursor_y = 0
        self.scroll_y = 0  
        self.u = 0 
        self.h = True # Highlighting Toggle
        
        self.styles = {
            'keyword': (r"\b(if|elif|else|for|while|break|continue|in|class|def|return|super|pass|lambda|yield|True|False|None|not|and|or|is|import|from|as|try|except|with|del|global)\b", Colors.YELLOW),
            'builtin': (r"\b(abs|all|any|ascii|bin|bool|breakpoint|bytearray|bytes|callable|chr|classmethod|compile|complex|delattr|dict|dir|divmod|enumerate|eval|exec|filter|float|format|frozenset|getattr|globals|hasattr|hash|help|hex|id|input|int|isinstance|issubclass|iter|len|list|locals|map|max|memoryview|min|next|object|oct|open|ord|pow|print|property|range|repr|reversed|round|set|setattr|slice|sorted|staticmethod|str|sum|super|tuple|type|vars|zip|__import__)\b", Colors.YELLOW),
            'bracket': (r'[\[\]\(\)\{\}]', Colors.YELLOW),
            'symbol': (r'([+\-*/%&|^=<>!~:;,.]{1,2})', Colors.RED),
            'comment': (r'#.*', Colors.BLUE),
            'string': (r'([\'"])(?:(?=(\\?))\2.)*?\1', Colors.GREEN),
        }

    def handle_input(self, key):
        event = Event(key)
        self.u = 0 
        modified = False
        
        if event.is_nav:
            if event.is_up and self.cursor_y > 0:
                self.cursor_y -= 1
                self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
            elif event.is_down and self.cursor_y < len(self.lines) - 1:
                self.cursor_y += 1
                self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
            elif event.is_left:
                if self.cursor_x > 0: self.cursor_x -= 1
                elif self.cursor_y > 0:
                    self.cursor_y -= 1
                    self.cursor_x = len(self.lines[self.cursor_y])
            elif event.is_right:
                if self.cursor_x < len(self.lines[self.cursor_y]): self.cursor_x += 1
                elif self.cursor_y < len(self.lines) - 1:
                    self.cursor_y += 1
                    self.cursor_x = 0

        elif event.is_backspace:
            modified = True
            if self.cursor_x > 0:
                line = self.lines[self.cursor_y]
                self.lines[self.cursor_y] = line[:self.cursor_x-1] + line[self.cursor_x:]
                self.cursor_x -= 1
            elif self.cursor_y > 0:
                prev_len = len(self.lines[self.cursor_y-1])
                self.lines[self.cursor_y-1] += self.lines.pop(self.cursor_y)
                self.cursor_y -= 1
                self.cursor_x = prev_len

        elif event.is_enter:
            modified = True
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x]
            self.lines.insert(self.cursor_y + 1, line[self.cursor_x:])
            self.cursor_y += 1
            self.cursor_x = 0

        elif event.is_char:
            modified = True
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x] + event.char + line[self.cursor_x:]
            self.cursor_x += 1
            
        if modified:
            self.emit("change", "\n".join(self.lines))

    def display(self, width, height):
        self.u += 1
        inner_h = height - 2
        
        if self.cursor_y < self.scroll_y:
            self.scroll_y = self.cursor_y
        elif self.cursor_y >= self.scroll_y + inner_h:
            self.scroll_y = self.cursor_y - inner_h + 1

        visible_lines = self.lines[self.scroll_y : self.scroll_y + inner_h]
        visible_text = "\n".join(visible_lines)
        
        rel_cursor_y = self.cursor_y - self.scroll_y
        cursor_1d = sum(len(line) + 1 for line in visible_lines[:rel_cursor_y]) + self.cursor_x
        
        # 1. Generate Highlighted String
        self.highlight(visible_text, cursor_1d)
        
        # 2. YOUR PADDING SKIP logic
        padding = "  "
        lines = self.text.splitlines()
        if not lines: lines = [""]
        
        padded_lines = [f"{padding if i != 0 else ''}{line}" for i, line in enumerate(lines)]
        self.text = "\n".join(padded_lines)
        
        return super().display(width, height)

    def highlight(self, text, cursor_idx):
        if not self.h:
            self.text = text
            return
            
        highlighted = ""
        current_pos = 0
        # Assuming self.u is your frame counter
        fps = statements.config.get("fps", 60)
        # Blink every half second (0.5s on, 0.5s off)
        blink_speed = fps // 2.5

        show_cursor = (self.u // blink_speed) % 2 == 0 and self.selected

        # Split everything including the newlines to keep current_pos accurate
        pattern = r'(\s+|[\[\]\(\)\{\}:;=\+\-\*\/]|#.*|[\'"].*?[\'"])'
        parts = re.split(pattern, text)

        for part in parts:
            if not part: continue
            
            # Use specific color if highlighting is ON, otherwise stick to White
            color = Colors.WHITE
            if self.h:
                if re.fullmatch(self.styles['keyword'][0], part): color = self.styles['keyword'][1]
                elif re.fullmatch(self.styles['builtin'][0], part): color = self.styles['builtin'][1]
                elif re.fullmatch(self.styles['bracket'][0], part): color = self.styles['bracket'][1]
                elif re.fullmatch(self.styles['symbol'][0], part): color = self.styles['symbol'][1]
                elif part.startswith("#"): color = self.styles['comment'][1]
                elif part.startswith(tuple("'\"")): color = self.styles['string'][1]

            part_len = len(part)
            
            # Cursor Logic: REVERSE the char at the cursor index
            if current_pos <= cursor_idx < current_pos + part_len and show_cursor:
                rel_idx = cursor_idx - current_pos
                char = part[rel_idx]
                
                # Make sure newlines show a blank space for the cursor
                cursor_char = char if char != '\n' else ' '
                cursor_visual = f"{Colors.REVERSE}{cursor_char}{Colors.RESET}"
                
                # Reconstruct part with highlighted char
                # If char was \n, we keep the \n AFTER the cursor_visual
                if char == '\n':
                    highlighted += f"{color}{part[:rel_idx]}{cursor_visual}\n{part[rel_idx+1:]}{Colors.RESET}"
                else:
                    highlighted += f"{color}{part[:rel_idx]}{cursor_visual}{color}{part[rel_idx+1:]}{Colors.RESET}"
            else:
                highlighted += f"{color}{part}{Colors.RESET}"
            
            current_pos += part_len
            
        # Trailing cursor (if at the end of the line/file)
        if cursor_idx >= len(text) and show_cursor:
            highlighted += f"{Colors.REVERSE} {Colors.RESET}"

        self.text = highlighted

    def set_cursor_pos(self, local_x, local_y):
        # We need to consider the padding "  " we add in display()
        inner_x = max(0, local_x - 1 - 2) # -1 for border, -2 for padding
        inner_y = max(0, local_y - 1)
        target_y = self.scroll_y + inner_y
        
        if target_y < len(self.lines):
            self.cursor_y = target_y
            self.cursor_x = min(inner_x, len(self.lines[self.cursor_y]))
        else:
            self.cursor_y = max(0, len(self.lines) - 1)
            self.cursor_x = len(self.lines[self.cursor_y])

class UIInput(Node):
    def __init__(self, weight, label=" URL: ", initial_text=""):
        super().__init__(weight=weight, focusable=True)
        self.label = label
        self.text = initial_text
        self.idx = len(initial_text) # The "Insertion Point"
        self.u = 0 # Your blink counter
        self.last_start = 0

    def handle_input(self, key):
        event = Event(key)
        modified = False
        if event.is_backspace:
            if self.idx > 0:
                self.text = self.text[:self.idx-1] + self.text[self.idx:]
                self.idx -= 1
                modified = True
        elif event.is_left and self.idx > 0:
            self.idx -= 1
        elif event.is_right and self.idx < len(self.text):
            self.idx += 1
        elif event.is_enter:
            self.emit("submit", self.text)
        elif event.is_char:
            self.text = self.text[:self.idx] + event.char + self.text[self.idx:]
            self.idx += 1
            modified = True
            
        if modified:
            self.emit("change", self.text)

    def set(self, text):
        self.text = text
        self.idx = len(text)

    def display(self, width, height):
        t_color = Theme.current_color_theme
        self.u += 1
        fps = statements.config.get("fps", 60)
        # Blink every half second (0.5s on, 0.5s off)
        blink_speed = fps // 2

        show_cursor = (self.u // blink_speed) % 2 == 0 and self.selected
        cursor = "_" if show_cursor else ""

        # Selection indicator from Theme
        prefix = (Theme.selected if self.selected else Theme.unselected)
        chars = Theme.focus_borders if self.selected else Theme.borders

        inner_w = max(0, width - 2 - len(self.label) - len(prefix))

        if self.idx < inner_w:
            start = 0
        else:
            start = self.idx - inner_w + 1

        self.last_start = start # Store for click processing

        visible_text = self.text[start:]
        adj_idx = self.idx - start

        before = visible_text[:adj_idx]
        after = visible_text[adj_idx+1:]

        # Apply Global Theme Secondary color to the text
        styled_label = f"{t_color.SECONDARY}{self.label}{Colors.RESET}"
        styled_before = f"{t_color.SECONDARY}{before}{Colors.RESET}"
        styled_after = f"{t_color.SECONDARY}{after}{Colors.RESET}"
        styled_prefix = f"{t_color.SECONDARY}{prefix}{Colors.RESET}"

        full_string = f"{styled_prefix}{styled_label}{styled_before}{cursor}{styled_after}"

        return wrap(full_string, w=width, h=height, chars=chars, color=self.color)
    
    def get_text(self):
        return self.text

    def set_cursor_pos(self, local_x, local_y):
        prefix_len = len(Theme.selected)
        label_len = len(self.label)
        start_x = 1 + prefix_len + label_len # 1 for border
        
        if local_x >= start_x:
            rel_x = local_x - start_x
            target_idx = self.last_start + rel_x
            self.idx = min(target_idx, len(self.text))
        else:
            self.idx = self.last_start
