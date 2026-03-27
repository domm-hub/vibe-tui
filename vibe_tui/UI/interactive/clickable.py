from ..base_widgets import UIBox
from ...base import wrap
from ...base.colors import Colors
from ...base.theme import Theme
from ...event.eventmanager import Event
import time

class UIButton(UIBox):
    def __init__(self, weight, text, title="", onclick=None, focusable=True):
        super().__init__(weight, text, title, focusable=focusable)
        self.onclick = onclick
        self.is_pressed = False 
        self.hovered = False
        self.lastclick = 0
        self.iter_pressed = 0
    
    def display(self, width, height):
        # Borders change when pressed OR selected
        if self.is_pressed:
            chars = Theme.BOLD
            self.is_pressed = False  # Reset after one frame of feedback
        elif self.selected:
            chars = Theme.focus_borders
        else:
            chars = Theme.borders

        prefix = Theme.selected if self.selected else Theme.unselected
        content = f"{prefix}{self.text}"
        
        # Apply hover visual cue
        if self.hovered and not self.selected:
            content = f"{Colors.REVERSE}{content}{Colors.RESET}"

        if self.color:
            content = self.color + content.replace('\n', Colors.RESET + '\n' + self.color) + Colors.RESET
        else:
            t_color = Theme.current_color_theme
            content = f"{t_color.SECONDARY}{content.replace(chr(10), Colors.RESET + chr(10) + t_color.SECONDARY)}{Colors.RESET}"

        return wrap(content, w=width, h=height, chars=chars, title=self.title)

    def press(self):
        # Allow pressing even if hovered but not selected, though usually click selects it first
        if self.selected or self.hovered:
            self.is_pressed = True
            if self.onclick: self.onclick()
            self.emit("click")

class UICheckbox(UIBox):
    def __init__(self, weight, text, title="", on_toggle=None, default_state=False):
        super().__init__(weight, text, title)
        self.on_toggle = on_toggle
        self.checked = default_state # Tracks the boolean state
        self.hovered = False
    
    def press(self):
        if self.selected or self.hovered:
            self.checked = not self.checked
            if self.on_toggle: self.on_toggle(self.checked)
            self.emit("toggle", self.checked)

    def display(self, width, height):
        chars = Theme.focus_borders if self.selected else Theme.borders

        # Checkbox visual from Theme
        icon = Theme.checked if self.checked else Theme.unchecked
        prefix = (Theme.selected if self.selected else Theme.unselected) + icon
            
        content = f"{prefix}{self.text}"
        
        if self.hovered and not self.selected:
            content = f"{Colors.REVERSE}{content}{Colors.RESET}"
        
        if self.color:
            content = self.color + content.replace('\n', Colors.RESET + '\n' + self.color) + Colors.RESET
        else:
            t_color = Theme.current_color_theme
            content = f"{t_color.SECONDARY}{content.replace(chr(10), Colors.RESET + chr(10) + t_color.SECONDARY)}{Colors.RESET}"

        return wrap(content, w=width, h=height, chars=chars, title=self.title)