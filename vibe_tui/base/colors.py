class Colors:
    # Use the octal escape sequence which is highly compatible
    ESC = "\033"
    RESET = f"{ESC}[0m"
    BOLD = f"{ESC}[1m"
    
    # Foreground
    BLACK = f"{ESC}[30m"
    RED = f"{ESC}[31m"
    GREEN = f"{ESC}[32m"
    YELLOW = f"{ESC}[33m"
    BLUE = f"{ESC}[34m"
    MAGENTA = f"{ESC}[35m"
    CYAN = f"{ESC}[36m"
    WHITE = f"{ESC}[37m"
    
    # Background
    BG_BLACK = f"{ESC}[40m"
    BG_WHITE = f"{ESC}[47m"

    @classmethod
    def all_fg(cls):
        return [cls.BLACK, cls.RED, cls.GREEN, cls.YELLOW, cls.BLUE, cls.MAGENTA, cls.CYAN, cls.WHITE]

    @staticmethod
    def apply(text, color_code):
        if not color_code: return text
        # Apply color and ensure it's reset, but also handle internal resets
        return f"{color_code}{text}{Colors.RESET}"