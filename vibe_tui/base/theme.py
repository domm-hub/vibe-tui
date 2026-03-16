from .colors import Colors

class Theme:
    """
    Central Theme Engine for Vibe-TUI.
    Controls borders, indicators, and default styling.
    """
    # Border Styles
    CURVED = {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"}
    SHARP  = {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│"}
    BOLD   = {"tl": "┏", "tr": "┓", "bl": "┗", "br": "┛", "h": "━", "v": "┃"}
    BLOCK  = {"tl": "█", "tr": "█", "bl": "█", "br": "█", "h": "▀", "v": "█"}
    ASCII  = {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|"}
    NONE   = {"tl": "", "tr": "", "bl": "", "br": "", "h": "", "v": ""}

    # Current Settings
    borders = CURVED
    focus_borders = BOLD
    
    # Indicators
    selected = "● "
    unselected = "○ "
    
    # Checkbox
    checked = "[X] "
    unchecked = "[ ] "
    
    # Colors
    primary = Colors.CYAN
    secondary = Colors.YELLOW
    accent = Colors.MAGENTA
    error = Colors.RED
    
    @classmethod
    def set_theme(cls, name: str):
        """Quickly swap the global border style."""
        themes = {
            "curved": cls.CURVED,
            "sharp": cls.SHARP,
            "bold": cls.BOLD,
            "block": cls.BLOCK,
            "ascii": cls.ASCII,
            "none": cls.NONE
        }
        if name.lower() in themes:
            cls.borders = themes[name.lower()]
