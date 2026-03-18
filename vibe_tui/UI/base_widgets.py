from ..node import Node
from ..base import wrap
from ..base.colors import Colors
from ..base.theme import Theme

class UIBox(Node):
    def __init__(self, weight, text, title="", focusable=True): 
        super().__init__(weight=weight, focusable=focusable) 
        self.text = text
        self.title = title
        self.selected = False 
    
    def set_text(self, text):
        self.text = text

    def display(self, width, height):
        # Determine focus indicator and border from Theme
        prefix = (Theme.selected if self.selected else Theme.unselected) if self.focusable else ""
        content = f"{prefix}{self.text}"
        
        chars = Theme.focus_borders if self.selected else Theme.borders
        
        # Apply Node-specific color first, otherwise apply Global Theme SECONDARY text color
        if self.color:
            content = self.color + content.replace('\n', Colors.RESET + '\n' + self.color) + Colors.RESET
        else:
            t_color = Theme.current_color_theme
            content = f"{t_color.SECONDARY}{content.replace(chr(10), Colors.RESET + chr(10) + t_color.SECONDARY)}{Colors.RESET}"
            
        return wrap(content, w=width, h=height, title=self.title, chars=chars)
    