from .colors import Colors, Theme as ColorTheme, DARK_THEME, LIGHT_BLUE_THEME

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
    
    # Legacy Colors (Keeping for backwards compatibility)
    primary = Colors.CYAN
    secondary = Colors.YELLOW
    accent = Colors.MAGENTA
    error = Colors.RED
    
    # New Dynamic Color Engine
    current_color_theme: ColorTheme = DARK_THEME

    @classmethod
    def set_color_theme(cls, theme: ColorTheme):
        """Globally swap the color palette for all nodes."""
        cls.current_color_theme = theme
        
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

