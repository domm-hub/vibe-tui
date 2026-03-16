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
        self.lastclick = 0
        self.iter_pressed = 0
    
    def display(self, width, height):
        # Borders change when pressed OR selected
        if self.is_pressed:
            chars = Theme.BOLD
            self.iter_pressed += 1
            if self.iter_pressed == 1:
                self.lastclick = time.time()
        elif self.selected:
            chars = Theme.SHARP
        else:
            self.iter_pressed = 0
            

            if time.time() - self.lastclick > 0.2:
                chars = Theme.borders

                
        
        prefix = Theme.selected if self.selected else Theme.unselected
            
        content = f"{prefix}{self.text}"
        
        if self.color:
            content = self.color + content.replace('\n', Colors.RESET + '\n' + self.color) + Colors.RESET

        return wrap(content, w=width, h=height, chars=chars, title=self.title)

    def press(self):
        if self.selected:
            # UIButton "press" usually triggers an action and flashes is_pressed
            self.is_pressed = True
            # Legacy callback support
            if self.onclick: self.onclick()
            # New signal system
            self.emit("click")

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

        if self.color:
            content = self.color + content.replace('\n', Colors.RESET + '\n' + self.color) + Colors.RESET

        return wrap(content, w=width, h=height, chars=chars, title=self.title)


class UICheckbox(UIBox):
    def __init__(self, weight, text, title="", on_toggle=None, default_state=False):
        super().__init__(weight, text, title)
        self.on_toggle = on_toggle
        self.checked = default_state # Tracks the boolean state
    
    def press(self):
        if self.selected:
            self.checked = not self.checked
            # Legacy callback support
            if self.on_toggle: self.on_toggle(self.checked)
            # New signal system
            self.emit("toggle", self.checked)

    def display(self, width, height):
        chars = Theme.focus_borders if self.selected else Theme.borders

        # Checkbox visual from Theme
        icon = Theme.checked if self.checked else Theme.unchecked
        prefix = (Theme.selected if self.selected else Theme.unselected) + icon
            
        content = f"{prefix}{self.text}"
        
        if self.color:
            content = self.color + content.replace('\n', Colors.RESET + '\n' + self.color) + Colors.RESET

        return wrap(content, w=width, h=height, chars=chars, title=self.title)

    def press(self):
        self.checked = not self.checked
        if self.on_toggle: self.on_toggle(self.checked)
        self.emit("change", self.checked)