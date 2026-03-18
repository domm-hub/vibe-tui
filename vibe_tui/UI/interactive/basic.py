import subprocess

from ..base_widgets import UIBox
from ...base import wrap
from ...base.colors import Colors
from ...base.theme import Theme
from ...event.eventmanager import Event
from ...layouts import UiContainerHorizontal, UiContainerVertical
from ...node import Node, Tab
from .clickable import UIButton

class UISelect(UIBox):
    def __init__(self, weight, options=None, title=""):
        super().__init__(weight=weight, text="", title=title)
        self.options = options if options is not None else ["Option 1", "Option 2", "Option 3"]
        self.selection = 0    # The currently highlighted item index
        self.scroll_l = 0     # The index of the top-most visible item (scroll offset)
    
    def handle_input(self, key):
        if not self.options: return
        event = Event(key)
        modified = False
        if event.is_up and self.selection > 0:
            self.selection -= 1
            modified = True
            if self.selection < self.scroll_l:
                self.scroll_l = self.selection
                
        elif event.is_down and self.selection < len(self.options) - 1:
            self.selection += 1
            modified = True
            
        if modified:
            self.emit("change", self.get_selected_item())

    def get_selected_item(self):
        if not self.options: return None
        return self.options[self.selection]
    
    def display(self, width, height):
        # 1. Calculate how many items can actually fit in the box
        # Subtracting 2 for top/bottom borders and 1 for the new percentage line
        available_lines = height - 3 
        if self.title:
            available_lines -= 3 
        available_lines = max(1, available_lines)

        # 2. Adjust scrolling logic (Keep selection in view)
        if self.selection >= self.scroll_l + available_lines:
            self.scroll_l = self.selection - available_lines + 1
        elif self.selection < self.scroll_l:
            self.scroll_l = self.selection

        # 3. Calculate Percentage and build the Dashed Track
        total_items = len(self.options)
        if total_items <= 1:
            perc = 100
        else:
            perc = int((self.selection / (total_items - 1)) * 100)

        # Calculate padding for dashes (width minus [00] and spacing)
        # We subtract ~10 to account for borders and the "[00]" text
        padding_size = (width - 10) // 2
        dashes = "-" * max(0, padding_size)
        percent_line = f"{Colors.DIM}{dashes} [{perc:02d}%] {dashes}-{Colors.RESET}"

        # 4. Slice the options for the current scroll window
        visible_options = self.options[self.scroll_l : self.scroll_l + available_lines]
        t_color = Theme.current_color_theme
        
        # 5. Build the text content array
        res = [percent_line]
        
        # Focus indicator for the whole widget
        widget_prefix = Theme.selected if self.selected else Theme.unselected
        res.append(f"{t_color.SECONDARY}{widget_prefix}{Colors.RESET}")

        for i, option_text in enumerate(visible_options):
            absolute_index = self.scroll_l + i 
            if absolute_index == self.selection:
                # Highlighted selection with arrow
                line = f" {t_color.ACCENT}▶{Colors.RESET}  {Colors.REVERSE}{option_text}{Colors.RESET}"
            else:
                # Standard dimmed option
                line = f"    {t_color.SECONDARY}{option_text}{Colors.RESET}"
            res.append(line)

        # Join content into final string
        content = "\n".join(res)
        
        # Select border style based on focus
        chars = Theme.focus_borders if self.selected else Theme.borders
        
        final_text = content

        # Apply global widget coloring if defined
        if self.color:
             final_text = self.color + final_text.replace('\n', Colors.RESET + '\n' + self.color) + Colors.RESET

        # Use your custom wrap function to render the final UIBox
        return wrap(final_text, w=width, h=height, chars=chars, title=self.title)


class TabManagerH(UiContainerHorizontal):
    def __init__(self, tabs: list[Tab], weight):
        super().__init__(weight)
        self.tabs = tabs
        self.active_index = 0
        self.focusable = True
        self._rebuild_nodes()

    def handle_input(self, key):
        event = Event(key)
        modified = False
        if event.is_left:
            self.set_active((self.active_index - 1) % len(self.tabs))
            modified = True
        elif event.is_right:
            self.set_active((self.active_index + 1) % len(self.tabs))
            modified = True
            
        if modified:
            self.emit("change", self.active_index)

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
            # A child button is "visually selected" ONLY if the manager is selected AND it's the active index
            node.selected = (self.selected and i == self.active_index)
                
        return super().display(width, height)

class UIScrollText(Node):
    def __init__(self, weight, text="", title="", show_line_numbers=False, wrap=True):
        super().__init__(weight=weight, focusable=True)
        self.text = text
        self.title = title
        self.show_line_numbers = show_line_numbers
        self.wrap = wrap
        self.scroll_y = 0 
        self._lines = text.splitlines()

    def set_text(self, new_text):
        self.text = new_text
        self._lines = new_text.splitlines()
        self.scroll_y = 0

    def handle_input(self, key):
        if not self._lines: return
        event = Event(key)
        if event.is_up and self.scroll_y > 0:
            self.scroll_y -= 1
        elif event.is_down and self.scroll_y < len(self._lines) - 1:
            self.scroll_y += 1

    def display(self, width, height):
        t_color = Theme.current_color_theme
        
        inner_h = max(0, height - 2)
        if self.title:
            inner_h -= 1 

        max_scroll = max(0, len(self._lines) - inner_h)
        self.scroll_y = min(self.scroll_y, max_scroll)
        
        visible_lines = self._lines[self.scroll_y : self.scroll_y + inner_h]
        
        # Selection indicator from Theme
        prefix = Theme.selected if self.selected else Theme.unselected
        
        formatted_lines = []
        if self.show_line_numbers:
            # Use a fixed minimum padding so different files align consistently
            pad_len = max(4, len(str(len(self._lines)))) + 1
            for i, line in enumerate(visible_lines):
                actual_line_num = self.scroll_y + i + 1
                num_str = f"{actual_line_num:>{pad_len}} | "
                # Apply ACCENT for line numbers and SECONDARY for text
                formatted_lines.append(f"{t_color.ACCENT}{num_str}{Colors.RESET}{t_color.SECONDARY}{line}{Colors.RESET}")
        else:
            # Apply SECONDARY to visible lines
            formatted_lines = [f"{t_color.SECONDARY}{line}{Colors.RESET}" for line in visible_lines]
            
        content_to_wrap = f"{t_color.SECONDARY}{prefix}{Colors.RESET}\n"
        content_to_wrap += "\n".join(formatted_lines) if formatted_lines else ""
        
        display_title = self.title
        if max_scroll > 0:
            percent = int((self.scroll_y / max_scroll) * 100) if max_scroll > 0 else 100
            scroll_indicator = f" {percent}% ↓ " if percent < 100 else " Bot "
            display_title = f"{self.title} {scroll_indicator}"

        chars = Theme.focus_borders if self.selected else Theme.borders
        wrap_mode = "wrap" if self.wrap else "truncate"

        return wrap(content_to_wrap, w=width, h=height, chars=chars, title=display_title, title_pos="center", mode=wrap_mode)

class UITerminal(UiContainerVertical):
    def __init__(self, weight=1, title=" TERMINAL "):
        super().__init__(weight=weight)
        self.title = title
        from ..interactive.textinput import UIInput
        self.output = UIScrollText(weight=10, title=title, show_line_numbers=False, wrap=True)
        self.cmd_input = UIInput(weight=1, label=" $ ", initial_text="")
        
        self.add(self.output)
        self.add(self.cmd_input)
        
        # Listen for Enter on the input field
        def handle_submit(cmd):
            if cmd:
                self.run_command(cmd)
                self.cmd_input.set_text("")
        self.cmd_input.on("submit", handle_submit)
        
        self.history = [f"{Colors.BOLD}Vibe-TUI Terminal Session{Colors.RESET}", "Type 'help' for commands", ""]
        self._update_output()

    def run_command(self, cmd):
        self.history.append(f"{Colors.CYAN}$ {cmd}{Colors.RESET}")
        
        if cmd == "clear":
            self.history = []
        elif cmd == "help":
            self.history.append("Available TUI commands: clear, help")
            self.history.append("System commands are executed via shell.")
        else:
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                if result.stdout:
                    self.history.extend(result.stdout.splitlines())
                if result.stderr:
                    self.history.extend([f"{Colors.RED}{l}{Colors.RESET}" for l in result.stderr.splitlines()])
                if not result.stdout and not result.stderr:
                    self.history.append(f"{Colors.YELLOW}(No output){Colors.RESET}")
            except Exception as e:
                self.history.append(f"{Colors.RED}Error: {e}{Colors.RESET}")
        
        self._update_output()

    def _update_output(self):
        self.output.set_text("\n".join(self.history))
        # Attempt to scroll to bottom
        self.output.scroll_y = max(0, len(self.output._lines) - 1)
