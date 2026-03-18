# Vibe-TUI

A TUI library based in pure python that uses weighting to align your program perfectly.

![Version](https://img.shields.io/badge/version-0.3.0--Beta-orange)
![Creator](https://img.shields.io/badge/creator-Adam%20Hany-blue)

### Why should I use this?
- No `asyncio`: Do what you want and manage as you like and display when you're finished; no rush here!
- Weight based alignment: Remove the hassle of calculating widths and heights to the weight system! (I don't see hackers need to be game devs to make good TUIs)

### What Nodes (or widgets) can I use?
- `UIBox(Node)`: A basic container box.
- `UIImage(Node)`: Displays an image as block characters (requires `term-image` and `Pillow`).
- `PyCodeText(UIBox)` (In progress): Python text editor widget.
- `UILabel(UIBox)`: A box without edges, used for text display.
- `UIBar(UIBox)`: Loading bar, requires vibe_loadbar to be installed.
- `ColorPicker(Node)`: A color selection widget.
- `UICheckbox(UIBox)`: A checkbox widget.
- `UIButton(UIBox)`: A clickable button.
- `UIInput(Node)`: A text input field.
- `UISelect(UIBox)`: A selection/list manager.
- `TabManagerH(UiContainerHorizontal)`: A horizontal tab manager.
- `UIScrollText(Node)`: A scrollable text view.
- `UIEditor(UIBox)`: A full-featured text editor.
- `UITerminal(UiContainerVertical)`: A terminal emulator widget.
- `UITree(UIBox)`: A tree view widget.
- `UIToast(Node)`: A toast notification overlay.
- `UIModal(Node)`: A basic modal overlay.
- `UIModalNode(UIModal)`: A modal that can contain another widget.
- `CanvasNode(Node)`: A canvas for custom drawing.
and more...

### What layouts can I use?
- `UiContainerHorizontal(Node)`: Horizontal layout.
- `UiContainerVertical(Node)`: Vertical layout.

You can also use `FocusManager` to manage Node focus.

### File Structure:

```
.
├── architecture.svg
├── pyproject.toml
├── README.md
├── vibe_browser.py
├── example.py
└── vibe_tui
    ├── UI
    │   ├── __init__.py
    │   ├── base_widgets.py
    │   ├── interactive
    │   │   ├── __init__.py
    │   │   ├── clickable.py
    │   │   ├── images
    │   │   │   ├── __init__.py
    │   │   │   └── image.py
    │   │   └── textinput.py
    │   └── widgets.py
    ├── __init__.py
    ├── base
    │   ├── __init__.py
    │   ├── basic.py
    │   ├── colors.py
    │   └── theme.py
    ├── event
    │   └── eventmanager.py
    ├── keyinput
    │   ├── __init__.py
    │   └── key.py
    ├── layouts
    │   ├── __init__.py
    │   └── baselayouts.py
    ├── managers
    │   ├── __init__.py
    │   ├── app.py
    │   └── manager.py
    ├── node
    │   ├── __init__.py
    │   └── basenode.py
    └── statements.py
```

### Class structure:
![class](architecture.svg)

### New:
- `VibeApp()` class makes a custom app for you without having to manage the event loop.

### Example code:

<details>
<summary>Click to view the code</summary>

```python
from vibe_tui import (
    VibeApp,
    UiContainerVertical,
    UiContainerHorizontal,
    UISelect,
    UIScrollText,
    UIInput,
    UILabel,
    Colors,
    Theme
)
import random
import string
from vibe_tui.base.colors import LIGHT_BLUE_THEME

Theme.set_color_theme(LIGHT_BLUE_THEME)

class SimpleApp:
    def __init__(self):
        # Sample data for demonstration
        self.all_items = items = [
            f"root/{'sys' if i % 3 == 0 else 'usr'}/{i:02d}/{''.join(random.choices(string.ascii_lowercase, k=12))}.cfg"
            for i in range(123)
        ]
        
        # 2. Define Layout
        self.root = UiContainerVertical()
        
        # Header with bold colors
        self.header = UILabel(weight=1, text=f" {Colors.BOLD}{Colors.BLUE}VIBE-TUI ENHANCED DEMO{Colors.RESET}")
        
        # Interactive Search/Filter bar
        self.search_bar = UIInput(weight=1, label="   Filter: ")
        
        # Main content area using weights (1:2 ratio)
        self.main_layout = UiContainerHorizontal(weight=8)
        self.list_box = UISelect(weight=1, title=" SELECTOR ")
        self.preview_box = UIScrollText(weight=2, title=" PREVIEW ", show_line_numbers=True)
        
        self.main_layout.add(self.list_box).add(self.preview_box)
        
        # Informative Footer
        self.footer = UILabel(weight=1, text=f" {Colors.DIM}Press 'q' to Quit | Tab: Switch Focus | Arrows: Navigate{Colors.RESET}")

        # Assemble the UI tree
        self.root.add(self.header).add(self.search_bar).add(self.main_layout).add(self.footer)

        # 3. Setup Logic & Events
        self.list_box.options = self.all_items
        
        # Bind events: Update preview on selection, and filter on search change
        self.list_box.on("change", self.on_selection_change)
        self.search_bar.on("change", self.on_search_change)

        # 4. Initialize the App Engine
        self.app = VibeApp(self.root)
        self.on_selection_change(None) # Initial preview load

    def on_selection_change(self, _):
        """Updates the preview pane based on the current selection."""
        if not self.list_box.options:
            self.preview_box.set_text("\n   No matches found.")
            return
            
        selected = self.list_box.options[self.list_box.selection]
        details = f"{Colors.BOLD}Details for:{Colors.RESET} {Colors.CYAN}{selected}{Colors.RESET}\n"
        details += "═" * 40 + "\n\n"
        details += "This UI is built using weight-based alignment,\n"
        details += "ensuring it scales perfectly with your terminal size.\n\n"
        details += f"Current Index: {Colors.YELLOW}{self.list_box.selection}{Colors.RESET}\n"
        details += f"Status: {Colors.GREEN}Active{Colors.RESET}" if self.list_box.selection % random.choice([i for i in range(1, 16)]) != 0 else f"Status: {Colors.RED}DISABLED{Colors.RESET}"
        
        self.preview_box.set_text(details)

    def on_search_change(self, query):
        """Filters the list selection as you type."""
        filtered = [item for item in self.all_items if query.lower() in item.lower()]
        self.list_box.options = filtered
        
        # Ensure selection index remains valid
        if self.list_box.selection >= len(filtered):
            self.list_box.selection = max(0, len(filtered) - 1)
        self.on_selection_change(None)

    def run(self):
        """Extends the input handler to support global shortcuts."""
        original_handle = self.app.fm.handle_input
        
        def custom_handle(key):
            # Global quit shortcut (when not typing in the search bar)
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
```
</details>

Made with **time** and `code` by **Adam Hany**
