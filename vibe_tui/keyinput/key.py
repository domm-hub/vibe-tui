class Key:
    """
    Unified Key Mapping for Vibe-TUI.
    Format: (ansi_code, string_name, ord_number)
    """
    # Navigation
    UP    = ("\x1b[A", "KEY_UP",    1001)
    DOWN  = ("\x1b[B", "KEY_DOWN",  1002)
    LEFT  = ("\x1b[D", "KEY_LEFT",  1003)
    RIGHT = ("\x1b[C", "KEY_RIGHT", 1004)
    
    # Actions
    ENTER     = ("\r",   "KEY_ENTER",     13)
    BACKSPACE = ("\x7f", "KEY_BACKSPACE", 127)
    TAB       = ("\t",   "KEY_TAB",        9)
    BTAB      = ("\x1b[Z", "KEY_BTAB",    1005) # Shift+Tab
    ESCAPE    = ("\x1b", "KEY_ESCAPE",    27)

    @classmethod
    def get(cls, raw):
        """
        Translates raw input into the (ansi, name, ord) tuple.
        If it's a standard character, it generates the tuple on the fly.
        """
        # 1. Check if it's a pre-defined special key
        for attr in dir(cls):
            val = getattr(cls, attr)
            if isinstance(val, tuple) and val[0] == raw:
                return val
        
        # 2. Handle standard characters (a, b, 1, !, etc.)
        if len(raw) == 1:
            return (raw, raw, ord(raw))
            
        # 3. Fallback for unknown sequences
        return (raw, "UNKNOWN", -1)