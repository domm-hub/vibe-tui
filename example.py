from vibe_tui import (
    VibeApp,
    UiContainerVertical,
    UiContainerHorizontal,
    UISelect,
    UIScrollText,
    UIInput,
    UILabel,
    Colors,
    Theme,
    wrap
)
import random
import string
from vibe_tui.base.colors import LIGHT_BLUE_THEME

# 1. Apply Global Theme
Theme.set_color_theme(LIGHT_BLUE_THEME)

# ---[ COMPONENT UPGRADE ]----------------------------------------------------
# We subclass UISelect to add the "Dashed Track" percentage feature
class EnhancedSelect(UISelect):
    def display(self, width, height):
        # Calculate available vertical space
        available_lines = height - 3  # -2 for borders, -1 for the track
        if self.title:
            available_lines -= 3 
        available_lines = max(1, available_lines)

        # Adjust scrolling
        if self.selection >= self.scroll_l + available_lines:
            self.scroll_l = self.selection - available_lines + 1
        elif self.selection < self.scroll_l:
            self.scroll_l = self.selection

        # ---[ THE VIBE TRACK ]---
        total_items = len(self.options)
        if total_items <= 1:
            perc = 100
        else:
            perc = int((self.selection / (total_items - 1)) * 100)

        # Dynamic dashes based on width
        padding_size = (width - 10) // 2
        dashes = "-" * max(0, padding_size)
        percent_line = f"{Colors.DIM}{dashes} [{perc:02d}%] {dashes}{Colors.RESET}"

        # Build Content
        visible_options = self.options[self.scroll_l : self.scroll_l + available_lines]
        t_color = Theme.current_color_theme
        
        res = [percent_line]
        widget_prefix = Theme.selected if self.selected else Theme.unselected
        res.append(f"{t_color.SECONDARY}{widget_prefix}{Colors.RESET}")

        for i, option_text in enumerate(visible_options):
            absolute_index = self.scroll_l + i 
            if absolute_index == self.selection:
                line = f" {t_color.ACCENT}▶{Colors.RESET}  {Colors.REVERSE}{option_text}{Colors.RESET}"
            else:
                line = f"    {t_color.SECONDARY}{option_text}{Colors.RESET}"
            res.append(line)

        # Final Render
        content = "\n".join(res)
        chars = Theme.focus_borders if self.selected else Theme.borders
        final_text = content
        if self.color:
             final_text = self.color + final_text.replace('\n', Colors.RESET + '\n' + self.color) + Colors.RESET

        return wrap(final_text, w=width, h=height, chars=chars, title=self.title)

# ---[ MAIN APP ]-------------------------------------------------------------
class SimpleApp:
    def __init__(self):
        # ---------------------------------------------------------
        # OPTIMIZATION 1: Fast Startup (The "Pool" Method)
        # Instead of calling random 3 million times, we reuse a pool.
        # ---------------------------------------------------------
        print("Generating data pool...") 
        pool_size = 10000
        suffix_pool = [''.join(random.choices(string.ascii_lowercase, k=12)) for _ in range(pool_size)]
        
        self.all_items = [
            f"root/{'sys' if i % 3 == 0 else 'usr'}/{i:02d}/{suffix_pool[i % pool_size]}.cfg"
            for i in range(30 * 10000000) # 300 Million Items
        ]

        # ---------------------------------------------------------
        # OPTIMIZATION 2: Pre-Computed Search Cache
        # We store the lowercase version ONCE to avoid doing it 
        # inside the search loop. This uses ~200MB RAM but is instant.
        # ---------------------------------------------------------
        print("Building search cache...")
        self._search_cache = [item.lower() for item in self.all_items]
        
        # 2. Define Layout
        self.root = UiContainerVertical()
        self.header = UILabel(weight=1, text=f" {Colors.BOLD}{Colors.BLUE}VIBE-TUI ENHANCED DEMO{Colors.RESET}")
        self.search_bar = UIInput(weight=1, label="   Filter: ")
        
        self.main_layout = UiContainerHorizontal(weight=8)
        
        # Use our new EnhancedSelect instead of the standard UISelect
        self.list_box = EnhancedSelect(weight=1, title=" SELECTOR ")
        self.preview_box = UIScrollText(weight=2, title=" PREVIEW ", show_line_numbers=True)
        
        self.main_layout.add(self.list_box).add(self.preview_box)
        self.footer = UILabel(weight=1, text=f" {Colors.DIM}Press 'q' to Quit | Tab: Switch Focus | Arrows: Navigate{Colors.RESET}")

        self.root.add(self.header).add(self.search_bar).add(self.main_layout).add(self.footer)

        # 3. Setup Logic & Events
        self.list_box.options = self.all_items
        self.list_box.on("change", self.on_selection_change)
        self.search_bar.on("change", self.on_search_change)

        self.app = VibeApp(self.root)
        self.on_selection_change(None)

    def on_selection_change(self, _):
        """Updates the preview pane based on the current selection."""
        if not self.list_box.options:
            self.preview_box.set_text("\n   No matches found.")
            return
            
        # Safety check: Ensure selection is within bounds
        idx = self.list_box.selection
        if idx >= len(self.list_box.options):
            idx = len(self.list_box.options) - 1
            
        selected = self.list_box.options[idx]
        
        details = f"{Colors.BOLD}Details for:{Colors.RESET} {Colors.CYAN}{selected}{Colors.RESET}\n"
        details += "═" * 40 + "\n\n"
        details += "This UI is handling 300,000,000 items using\n"
        details += "pre-cached search and weight-based alignment.\n\n"
        details += f"Current Index: {Colors.YELLOW}{idx}{Colors.RESET}\n"
        
        # Pseudo-random status based on index (deterministic, no random calls needed)
        is_active = idx % 17 != 0 
        status_color = Colors.GREEN if is_active else Colors.RED
        status_text = "Active" if is_active else "DISABLED"
        details += f"Status: {status_color}{status_text}{Colors.RESET}"
        
        self.preview_box.set_text(details)

    def on_search_change(self, query):
        """
        OPTIMIZATION 3: The 'Zip' Search
        Scans the pre-lowered cache instead of lowering strings in real-time.
        """
        query_low = query.lower()
        
        # If query is empty, restore full list immediately
        if not query_low:
            self.list_box.options = self.all_items
            self.on_selection_change(None)
            return

        # The Zip Loop: Extremely fast linear scan
        filtered = []
        count = 0
        limit = 2000 # Hard limit to keep UI snappy even if 1M items match "a"
        
        for original, cached in zip(self.all_items, self._search_cache):
            if query_low in cached:
                filtered.append(original)
                count += 1
                if count >= limit:
                    break
        
        self.list_box.options = filtered
        self.list_box.selection = 0 # Reset selection to top
        self.on_selection_change(None)

    def run(self):
        original_handle = self.app.fm.handle_input
        
        def custom_handle(key):
            if key == 'q' and self.app.fm.current != self.search_bar:
                self.app.stop()
                return
            original_handle(key)
        
        self.app.fm.handle_input = custom_handle
        self.app.run()

if __name__ == "__main__":
    try:
        SimpleApp().run()
    except Exception as e:
        print(f"Error starting app: {e}")
