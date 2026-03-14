from ..node import Node
from ..base import wrap
from ..base.colors import Colors

class UIBox(Node):
    def __init__(self, weight, text, title="", focusable=True): 
        super().__init__(weight=weight, focusable=focusable) 
        self.text = text
        self.title = title
        self.selected = False 
    
    def display(self, width, height):
        if self.focusable:
            prefix = "● " if self.selected else "○ "
        else:
            prefix = ""
        content = f"{prefix}{self.text}" if self.title else f"{prefix}{self.text}"
        
        # Color is applied to the content *before* wrapping to keep borders clean
        if self.color:
            content = self.color + content.replace('\n', Colors.RESET + '\n' + self.color) + Colors.RESET
            
        return wrap(content, w=width, h=height, title=self.title)

        
    def display(self, width, height):
        # 1. Determine the correct prefix based on FocusManager state
        pr = "● " if self.selected else "○ "
        
        # 2. Clean the text of any existing icons to prevent "● ○ ● ○ Code"
        clean_text = self.text.lstrip("● ").lstrip("○ ")
        
        # 3. Combine them for the wrap function
        # Note: Avoid \n here unless you want the code to start on the second line
        display_text = f"{pr}\n{clean_text}"
        
        return wrap(display_text, w=width, h=height, title=self.title, title_pos="center")
    