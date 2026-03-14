from ..node import Node, Tab
from ..base import wrap
from ..base.colors import Colors
from ..layouts import UiContainerHorizontal, UiContainerVertical
from .interactive import UIButton
from .base_widgets import UIBox
import re


        
class UILabel(UIBox):
    def __init__(self, weight, text):
        self.text = text
        super().__init__(weight, text)
        
    def display(self, width, height):
        return wrap(self.text, width, height, {"tr": "", "tl": "", "br": "", "bl": "", "v": "", "h": ""})
    

          
class UIBar(UIBox):
    def __init__(self, weight, finish, label="CHILLING", **kwrgs_l):
        try:
            from vibe_load import Loading
        except ImportError:
            raise ImportError("The progress bar module couldnt be found.")
        super().__init__(weight, "")
        self.load = Loading(iterable=None, finish=finish, action=label, print_cli=False, **kwrgs_l)
        self.width = 80

    def display(self, w, h):
        self.width = w
        return wrap(self.text, w=w, h=h)
    
    def update_bar(self, progress):
        self.text = self.load.update(progress, widtha=self.width - 10)
    
class ColorPicker(Node):
    def __init__(self, weight=1):
        super().__init__(weight=weight)
        self.colors = Colors.all_fg()
        self.index = 0
    
    def next_color(self):
        self.index = (self.index + 1) % len(self.colors)
    
    def prev_color(self):
        self.index = (self.index - 1) % len(self.colors)

    def current_color(self):
        return self.colors[self.index]

    def display(self, width, height):
        content = "USE LEFT/RIGHT ARROWS\nTO PICK A COLOUR\n\n"
        for i, color in enumerate(self.colors):
            if i == self.index:
                # Highlight the selected color box
                block = f"{Colors.BG_WHITE}  {Colors.RESET}" 
                label = f" < {Colors.apply('SELECTED', color)} >"
                content += f" {block} {label}\n"
            else:
                block = f"{color}{Colors.BG_BLACK}  {Colors.RESET}"
                content += f" {block}\n"
        
        # ColorPicker content already has ANSI codes, so just wrap it
        return wrap(content, width, height)

                
class UISelect(UIBox):
    def __init__(self, weight, options=None, title=""):
        super().__init__(weight=weight, text="", title=title)
        self.options = options if options is not None else ["Option 1", "Option 2", "Option 3"]
        self.selection = 0    # The currently highlighted item index
        self.scroll_l = 0     # The index of the top-most visible item (scroll offset)
    
    def handle_input(self, key):
        if not self.options: return
        if key == "KEY_UP" and self.selection > 0:
            self.selection -= 1
            if self.selection < self.scroll_l:
                self.scroll_l = self.selection
                
        elif key == "KEY_DOWN" and self.selection < len(self.options) - 1:
            self.selection += 1

    def get_selected_item(self):
        if not self.options: return None
        return self.options[self.selection]
    
    def display(self, width, height):
        # Calculate how many items can actually fit in the box
        available_lines = height - 2
        if self.title:
            available_lines -= 2 
            
        available_lines = max(1, available_lines)

        # Adjust scrolling
        if self.selection >= self.scroll_l + available_lines:
            self.scroll_l = self.selection - available_lines + 1
        elif self.selection < self.scroll_l:
            self.scroll_l = self.selection

        # Slice the options
        visible_options = self.options[self.scroll_l : self.scroll_l + available_lines]
        
        # Build the text content
        res = []
        # Focus indicator for the whole widget
        widget_prefix = "● " if self.selected else "○ "
        res.append(widget_prefix)

        for i, option_text in enumerate(visible_options):
            absolute_index = self.scroll_l + i 
            if absolute_index == self.selection:
                line = f"  > {Colors.YELLOW}{option_text}{Colors.RESET}"
            else:
                line = f"    {option_text}"
            res.append(line)

        content = "\n".join(res)
        
        # Curved borders
        chars = {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"}
        
        final_text = content

        if self.color:
             final_text = self.color + final_text.replace('\n', Colors.RESET + '\n' + self.color) + Colors.RESET

        return wrap(final_text, w=width, h=height, chars=chars, title=self.title)
    

class TabManagerH(UiContainerHorizontal):
    def __init__(self, tabs: list[Tab], weight):
        super().__init__(weight)
        self.tabs = tabs
        self.active_index = 0
        self.focusable = True
        self._rebuild_nodes()

    def handle_input(self, key):
        if key == "KEY_LEFT":
            self.set_active((self.active_index - 1) % len(self.tabs))
        elif key == "KEY_RIGHT":
            self.set_active((self.active_index + 1) % len(self.tabs))

    def _rebuild_nodes(self):
        """
        Creates the UIButton instances for each tab.
        Set focusable=False so FocusManager ignores them.
        """
        self.reset()
        for i, tab in enumerate(self.tabs):
            def create_click_handler(idx):
                return lambda: self.set_active(idx)
            
            # Tabs are managed separately (e.g. via arrows), so we hide them from FocusManager
            btn = UIButton(1, tab.title, onclick=create_click_handler(i), focusable=False)
            self.add(btn)

    def add_tab(self, tab: Tab):
        self.tabs.append(tab)
        self._rebuild_nodes()
    
    def delete_tab(self, index):
        if 0 <= index < len(self.tabs) and len(self.tabs) > 1:
            self.tabs.pop(index)
            self.active_index = min(self.active_index, len(self.tabs) - 1)
            self._rebuild_nodes()

    def set_active(self, index):
        """Sets which tab's content is currently displayed."""
        if 0 <= index < len(self.tabs):
            self.active_index = index

    def get_active_content(self):
        return self.tabs[self.active_index].content

    def display(self, width, height):
        for i, node in enumerate(self.nodes):
            if i == self.active_index:
                if not node.selected:
                    node.selected = True

            else:
                node.selected = False
                
        return super().display(width, height)

class UIScrollText(Node):
    def __init__(self, weight, text="", title="", show_line_numbers=False):
        super().__init__(weight=weight, focusable=True)
        self.text = text
        self.title = title
        self.show_line_numbers = show_line_numbers
        self.scroll_y = 0 
        self._lines = text.splitlines()

    def set_text(self, new_text):
        self.text = new_text
        self._lines = new_text.splitlines()
        self.scroll_y = 0

    def handle_input(self, key):
        if not self._lines: return
        if key == "KEY_UP" and self.scroll_y > 0:
            self.scroll_y -= 1
        elif key == "KEY_DOWN" and self.scroll_y < len(self._lines) - 1:
            self.scroll_y += 1

    def display(self, width, height):
        inner_h = max(0, height - 2)
        if self.title:
            inner_h -= 1 

        max_scroll = max(0, len(self._lines) - inner_h)
        self.scroll_y = min(self.scroll_y, max_scroll)
        
        visible_lines = self._lines[self.scroll_y : self.scroll_y + inner_h]
        
        # Selection indicator
        prefix = "● " if self.selected else "○ "
        
        formatted_lines = []
        if self.show_line_numbers:
            pad_len = len(str(len(self._lines))) 
            for i, line in enumerate(visible_lines):
                actual_line_num = self.scroll_y + i + 1
                num_str = f"{actual_line_num:>{pad_len}} | "
                formatted_lines.append(f"{Colors.YELLOW}{num_str}{Colors.RESET}{line}")
        else:
            formatted_lines = visible_lines

        content_to_wrap = "\n".join([prefix + line for line in formatted_lines]) if formatted_lines else prefix
        
        display_title = self.title
        if max_scroll > 0:
            percent = int((self.scroll_y / max_scroll) * 100) if max_scroll > 0 else 100
            scroll_indicator = f" {percent}% ↓ " if percent < 100 else " Bot "
            display_title = f"{self.title} {scroll_indicator}"

        # Curved borders always
        chars = {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"}

        return wrap(content_to_wrap, w=width, h=height, chars=chars, title=display_title, title_pos="center")
    def __init__(self, weight, text="", title="", show_line_numbers=False):
        super().__init__(weight=weight, focusable=True)
        self.text = text
        self.title = title
        self.show_line_numbers = show_line_numbers
        self.scroll_y = 0  # Which line is currently at the top of the box
        
        # We pre-calculate the lines to avoid doing it on every frame
        self._lines = text.splitlines()

    def set_text(self, new_text):
        """Helper to update text and reset scroll."""
        self.text = new_text
        self._lines = new_text.splitlines()
        self.scroll_y = 0

    def handle_input(self, key):
        """Allows the user to scroll through the text when focused."""
        if not self._lines: return

        if key == "KEY_UP" and self.scroll_y > 0:
            self.scroll_y -= 1
            
        elif key == "KEY_DOWN":
            # We don't know the exact height here, so we cap it loosely.
            # The display() function will clamp it perfectly later.
            if self.scroll_y < len(self._lines) - 1:
                self.scroll_y += 1
                
        # Optional: Add PAGE_UP and PAGE_DOWN if your get_keypress supports them
        # elif key == "PAGE_UP":
        #     self.scroll_y = max(0, self.scroll_y - 10)
        # elif key == "PAGE_DOWN":
        #     self.scroll_y = min(len(self._lines) - 1, self.scroll_y + 10)

    def display(self, width, height):
        # 1. Calculate usable space inside the borders
        inner_h = max(0, height - 2)
        if self.title:
            inner_h -= 1 # Your wrap function accounts for the title bar

        # 2. Clamp the scroll so we don't scroll past the bottom
        # If the text is shorter than the box, scroll_y must be 0
        max_scroll = max(0, len(self._lines) - inner_h)
        self.scroll_y = min(self.scroll_y, max_scroll)

        # 3. Slice the text to only what fits in the viewport
        visible_lines = self._lines[self.scroll_y : self.scroll_y + inner_h]
        
        # 4. (Optional) Add line numbers
        formatted_lines = []
        if self.show_line_numbers:
            # Find how many digits the max line number has so we can pad cleanly
            pad_len = len(str(len(self._lines))) 
            for i, line in enumerate(visible_lines):
                actual_line_num = self.scroll_y + i + 1
                # Dark gray line numbers (assuming Colors.DARK_GRAY exists, or just use regular formatting)
                num_str = f"{actual_line_num:>{pad_len}} | "
                formatted_lines.append(f"{Colors.YELLOW}{num_str}{Colors.RESET}{line}")
        else:
            formatted_lines = visible_lines

        # 5. Join the lines back into a single string for the wrap function
        content_to_wrap = "\n".join(formatted_lines)
        
        # Add a scroll indicator to the title if there is hidden text
        display_title = self.title
        if max_scroll > 0:
            percent = int((self.scroll_y / max_scroll) * 100) if max_scroll > 0 else 100
            scroll_indicator = f" {percent}% ↓ " if percent < 100 else " Bot "
            display_title = f"{self.title} {scroll_indicator}"

        # 6. Set borders based on focus
        if self.selected:
            chars = {"tl": "┏", "tr": "┓", "bl": "┗", "br": "┛", "h": "━", "v": "┃"}
        else:
            chars = {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"}

        # Use your shiny new wrap function!
        return wrap(content_to_wrap, w=width, h=height, chars=chars, title=display_title, title_pos="center")
    
class UIModal(Node):
    def __init__(self, width_pct=0.5, height_pct=0.5, title="[ Modal ]", text=""):
        super().__init__(weight=1) # Weight doesn't matter much here
        self.width_pct = width_pct
        self.height_pct = height_pct
        self.title = title
        self.text = text
        self.is_active = False

    def display_over(self, screen_buffer, term_width, term_height):
        """
        Takes the fully rendered screen buffer and draws the modal over it.
        Returns the modified screen buffer.
        """
        if not self.is_active:
            return screen_buffer

        # 1. Calculate the modal's absolute dimensions
        modal_w = max(10, int(term_width * self.width_pct))
        modal_h = max(5, int(term_height * self.height_pct))

        # 2. Calculate the top-left starting position to center it
        start_x = (term_width - modal_w) // 2
        start_y = (term_height - modal_h) // 2

        # 3. Generate the modal's content using your existing wrap function
        # We use selected=True styling (thicker borders) to make it pop
        chars = {"tl": "┏", "tr": "┓", "bl": "┗", "br": "┛", "h": "━", "v": "┃"}
        
        # Apply a background color if your Colors class supports it, 
        # or just standard text to ensure it covers the background
        modal_content = wrap(
            self.text, 
            w=modal_w, 
            h=modal_h, 
            chars=chars, 
            title=self.title, 
            title_pos="center"
        )

        # 4. "Blit" (draw) the modal onto the screen buffer
        new_screen = list(screen_buffer) # Copy the buffer
        
        # We need a helper function to strip ANSI codes from the background line
        # so we can correctly overwrite the characters without breaking color formatting.
        import re
        ansi_regex = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
        
        for i, modal_line in enumerate(modal_content):
            buffer_y = start_y + i
            if 0 <= buffer_y < len(new_screen):
                bg_line = new_screen[buffer_y]
                
                # Strip ANSI from the background line to calculate visual length safely
                # (This is a simplified overlay that assumes the background line is exactly term_width wide)
                clean_bg = ansi_regex.sub('', bg_line)
                
                # If the background line has ANSI codes, this simple slicing might disrupt them.
                # A more robust approach rebuilds the line character by character, 
                # but this is usually sufficient for simple TUIs where the modal covers a solid block.
                
                # We slice the background before and after the modal
                left_part = clean_bg[:start_x]
                right_part = clean_bg[start_x + modal_w:]
                
                # Stitch it together: Left BG + Modal Line + Right BG
                # Note: We append Colors.RESET at the end to prevent modal colors bleeding into the right BG
                new_screen[buffer_y] = f"{left_part}{modal_line}{Colors.RESET}{right_part}"

        return new_screen