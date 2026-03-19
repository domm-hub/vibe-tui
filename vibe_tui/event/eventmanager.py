from ..keyinput import Key

class Event:
    def __init__(self, key):
        # Normalize input to (ansi, name, ord) tuple
        if isinstance(key, str):
            self.key = Key.get(key)
        else:
            self.key = key 
            
        # Basic properties for easy access
        self.raw = self.key[0] if isinstance(self.key, (tuple, list)) else self.key
        self.name = self.key[1] if isinstance(self.key, (tuple, list)) else "UNKNOWN"
        self.code = self.key[2] if isinstance(self.key, (tuple, list)) else -1

        # Boolean classifications
        self.is_tab = self.key == Key.TAB
        self.is_btab = self.key == Key.BTAB
        self.is_fc = self.is_tab or self.is_btab
        
        self.is_enter = self.key == Key.ENTER or self.raw == "\n"
        self.is_action = self.is_enter
        
        self.is_up = self.key == Key.UP
        self.is_down = self.key == Key.DOWN
        self.is_left = self.key == Key.LEFT
        self.is_right = self.key == Key.RIGHT
        self.is_nav = self.is_up or self.is_down or self.is_left or self.is_right
        
        self.is_backspace = self.key == Key.BACKSPACE
        self.is_escape = self.key == Key.ESCAPE
        
        # Character handling: is it a standard printable character?
        # A char is usually something Key.get couldn't find in special keys
        # but has length 1 and matches name/raw.
        self.is_char = (len(self.raw) == 1 and self.name == self.raw and 
                        not (self.is_nav or self.is_action or self.is_fc or 
                             self.is_backspace or self.is_escape))
        self.char = self.raw if self.is_char else None

    def get_val(self):
        return self.key

    def __eq__(self, other):
        """Allows direct comparison between Event objects and Key tuples."""
        if isinstance(other, (tuple, list)):
            return self.key == other
        return super().__eq__(other)

#