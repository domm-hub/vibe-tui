from ...base import wrap
from ...base.colors import Colors
from ...node import Node
from ...layouts import UiContainerHorizontal, UiContainerVertical
import re
from ..base_widgets import UIBox

class UIEditor(UIBox):
    def __init__(self, weight, text="", title=" EDITOR "):
        super().__init__(weight=weight, text=text, title=title, focusable=True)
        self.lines = text.splitlines() if text else [""]
        self.cursor_x = 0
        self.cursor_y = 0
        self.scroll_y = 0
        self.blink_counter = 0

    def handle_input(self, key):
        self.blink_counter = 0 # Reset blink on activity
        
        if key == "KEY_UP":
            if self.cursor_y > 0:
                self.cursor_y -= 1
                self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
        
        elif key == "KEY_DOWN":
            if self.cursor_y < len(self.lines) - 1:
                self.cursor_y += 1
                self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
        
        elif key == "KEY_LEFT":
            if self.cursor_x > 0:
                self.cursor_x -= 1
            elif self.cursor_y > 0:
                self.cursor_y -= 1
                self.cursor_x = len(self.lines[self.cursor_y])
        
        elif key == "KEY_RIGHT":
            if self.cursor_x < len(self.lines[self.cursor_y]):
                self.cursor_x += 1
            elif self.cursor_y < len(self.lines) - 1:
                self.cursor_y += 1
                self.cursor_x = 0

        elif key == "KEY_BACKSPACE":
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

        elif key == "KEY_ENTER":
            # Split line at cursor
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x]
            self.lines.insert(self.cursor_y + 1, line[self.cursor_x:])
            self.cursor_y += 1
            self.cursor_x = 0

        elif isinstance(key, str) and len(key) == 1:
            # Standard character insertion
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x] + key + line[self.cursor_x:]
            self.cursor_x += 1

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
        cursor_char = "█" if (self.blink_counter // 15) % 2 == 0 else " "
        
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
        if key in (127, 8, "\x7f"):
            if self.idx > 0:
                self.text = self.text[:self.idx-1] + self.text[self.idx:]
                self.idx -= 1
        elif key == "KEY_LEFT" and self.idx > 0:
            self.idx -= 1
        elif key == "KEY_RIGHT" and self.idx < len(self.text):
            self.idx += 1
        elif isinstance(key, str) and len(key) == 1:
            self.text = self.text[:self.idx] + key + self.text[self.idx:]
            self.idx += 1

    def display(self, width, height):
            self.u += 1
            cursor = "_" if (self.u // 10) % 2 == 0 else " "
            
            # Selection indicator
            prefix = "● " if self.selected else "○ "
            
            inner_w = max(0, width - 2 - len(self.label) - len(prefix))
            
            if self.idx < inner_w:
                start = 0
            else:
                start = self.idx - inner_w + 1
                
            visible_text = self.text[start:]
            adj_idx = self.idx - start 
            
            before = visible_text[:adj_idx]
            after = visible_text[adj_idx+1:]
            
            full_string = f"{prefix}{self.label}{before}{cursor}{after}"
            
            # Curved borders
            chars = {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"}
            
            return wrap(full_string, w=width, h=height, chars=chars, color=self.color)
        