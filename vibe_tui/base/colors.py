
from dataclasses import dataclass

@dataclass
class Theme:
    PRIMARY: str
    SECONDARY: str
    ACCENT: str
    SUCCESS: str = "\033[32m"
    ERROR: str = "\033[31m"

# Define your specific themes
# Using 195 for that "lighter again" blue you requested
LIGHT_BLUE_THEME = Theme(
    PRIMARY="\033[48;5;195;30m",   # Ultra light blue BG, Black text
    SECONDARY="\033[38;5;153m",    # Soft blue FG
    ACCENT="\033[1;34m"            # Bold Blue
)

DARK_THEME = Theme(
    PRIMARY="\033[48;5;235;37m",   # Dark grey BG, White text
    SECONDARY="\033[38;5;244m",    # Grey FG
    ACCENT="\033[1;36m"            # Bold Cyan
)

class Colors:
    ESC = "\033"
    RESET = f"{ESC}[0m"
    BOLD = f"{ESC}[1m"
    REVERSE = "\033[7m"
    
    # Foreground
    BLACK = f"{ESC}[30m"
    RED = f"{ESC}[31m"
    GREEN = f"{ESC}[32m"
    YELLOW = f"{ESC}[33m"
    BLUE = f"{ESC}[34m"
    MAGENTA = f"{ESC}[35m"
    CYAN = f"{ESC}[36m"
    WHITE = f"{ESC}[37m"
    UNDERLINE = f"{ESC}[4m2"
    DIM = f"{ESC}[2m"
    
    # Background
    BG_BLACK = f"{ESC}[40m"
    BG_WHITE = f"{ESC}[47m"

    @classmethod
    def all_fg(cls):
        return [cls.BLACK, cls.RED, cls.GREEN, cls.YELLOW, cls.BLUE, cls.MAGENTA, cls.CYAN, cls.WHITE]

    @staticmethod
    def apply(text, color_code):
        if not color_code: return text
        return f"{color_code}{text}{Colors.RESET}"

    @staticmethod
    def pill(text, theme_color):
        """Creates the one-line 'curved' effect using padding"""
        return f"{theme_color}  {text}  {Colors.RESET}"