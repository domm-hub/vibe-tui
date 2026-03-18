from ...base.theme import Theme
from ...base import wrap
from ...base.colors import Colors
from ..base_widgets import UIBox
from ...node import Node
from ...event.eventmanager import Event
import re


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
    
    def set_text(self, text):
        self.lines = text.splitlines() if text else [""]
        self.cursor_x = 0
        self.cursor_y = 0
        self.scroll_y = 0
    

class PyCodeText(UIBox):
    def __init__(self, weight, text="", title=""):
        super().__init__(weight=weight, text=text, title=title)
        self.python_keywords = ([
            # Control Flow
            "if", "elif", "else", "for", "while", "break", "continue", "in",
            
            # Structure & Definitions
            "class", "def", "return", "super", "pass", "lambda", "yield",
            
            # State & Logic
            "True", "False", "None", "not", "and", "or", "is",
            
            # Organization & Safety
            "import", "from", "as", "try", "except", "with", "del", "global"
        ], "yellow")
        
        self.brackets = ([
            "[", "]",
            "{", "}",
            "(", ")"
        ], 'yellow')
        self.symbols = ([
            ":", ";",
        ], 'white')

        self.str = ([
            '"', "'", 
        ], 'green')
        
        self.comments = (["#"], 'blue')
        
    def set(self, text, cursor_idx):
        # 1. We split while keeping the newlines intact
        # This regex splits by spaces/tabs but remembers the structure
        tokens = re.split(r'(\s+)', text)
        
        self.highlighted_text = ""
        current_len = 0
        
        for token in tokens:
            # Skip empty tokens from the split
            if not token: continue
            
            # 2. Check if this token is a word or just whitespace
            if token.strip():
                # Get the base color
                color = Colors.WHITE
                if token in self.python_keywords[0]: color = self.python_keywords[1]
                elif token in self.brackets[0]: color = self.brackets[1]
                elif token in self.symbols[0]: color = self.symbols[1]
                elif token.startswith("#"): color = self.comments[1]
                
                ansi_color = getattr(Colors, color.upper(), Colors.WHITE)
                
                # 3. Add Cursor logic: 
                # If the cursor index falls within this word, underline it
                word_end = current_len + len(token)
                if current_len <= cursor_idx < word_end:
                    self.highlighted_text += f"{ansi_color}{Colors.UNDERLINE}{token}{Colors.RESET} "
                else:
                    self.highlighted_text += f"{ansi_color}{token}{Colors.RESET}"
                
                current_len += len(token)
            else:
                # Keep the original whitespace (newlines/tabs)
                self.highlighted_text += token
                current_len += len(token)
                

        self.text = f"{self.highlighted_text}"
        

class UIInput(Node):
    def __init__(self, weight, label=" URL: ", initial_text=""):
        super().__init__(weight=weight, focusable=True)
        self.label = label
        self.text = initial_text
        self.idx = len(initial_text) # The "Insertion Point"
        self.u = 0 # Your blink counter

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

    def set_text(self, text):
        self.text = text
        self.idx = len(text)

    def display(self, width, height):
        t_color = Theme.current_color_theme
        self.u += 1
        cursor = "_" if (self.u // 10) % 2 == 0 else " "

        # Selection indicator from Theme
        prefix = (Theme.selected if self.selected else Theme.unselected)
        chars = Theme.focus_borders if self.selected else Theme.borders

        inner_w = max(0, width - 2 - len(self.label) - len(prefix))

        if self.idx < inner_w:
            start = 0
        else:
            start = self.idx - inner_w + 1

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