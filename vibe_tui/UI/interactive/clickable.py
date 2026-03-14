from ..base_widgets import UIBox
from ...base import wrap
from ...base.colors import Colors


class UIButton(UIBox):
    def __init__(self, weight, text, title="", onclick=None, focusable=True):
        super().__init__(weight, text, title, focusable=focusable)
        self.onclick = onclick
        self.is_pressed = False 
    
    def display(self, width, height):
        # Use curved borders always, no bold
        
        if self.is_pressed:
            chars = {
                "tl": "┏", 
                "tr": "┓", 
                "bl": "┗", 
                "br": "┛", 
                "h": "━", 
                "v": "┃"
            }
        else:
            chars = {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"}
        
        

        prefix = "● " if self.selected else "○ "
            
        content = f"{prefix}{self.text}" if self.title else f"{prefix}{self.text}"
        
        if self.color:
            content = self.color + content.replace('\n', Colors.RESET + '\n' + self.color) + Colors.RESET

        return wrap(content, w=width, h=height, chars=chars, title=self.title)
    
    def press(self):
        if self.selected:
            if not self.is_pressed:
                self.is_pressed = True
            else:
                self.is_pressed = False
            if self.onclick: self.onclick()
            
        
class UICheckbox(UIBox):
    def __init__(self, weight, text, title="", on_toggle=None, default_state=False):
        super().__init__(weight, text, title)
        self.on_toggle = on_toggle
        self.checked = default_state # Tracks the boolean state
    
    def display(self, width, height):
        # Curved borders
        chars = {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"}
        
        # Checkbox visual
        prefix = "[X] " if self.checked else "[ ] "
        if self.selected:
            prefix = "● " + prefix
        else:
            prefix = "○ " + prefix
            
        content = f"{prefix}{self.text}" if self.title else f"{prefix}{self.text}"
        
        if self.color:
            content = self.color + content.replace('\n', Colors.RESET + '\n' + self.color) + Colors.RESET

        return wrap(content, w=width, h=height, chars=chars, title=self.title)
    
    def press(self):
        # Toggle state on press
        if self.selected:
            self.checked = not self.checked
            if self.on_toggle: 
                self.on_toggle(self.checked) # Pass the new state to the callback
                