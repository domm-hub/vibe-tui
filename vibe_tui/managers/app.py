import os
import sys
import time
import select
import termios
import tty
from contextlib import contextmanager

class VibeApp:
    def __init__(self, root_node, modals=None, key_handler=None):
        """
        The Refined Vibe-TUI Engine.
        """
        self.root = root_node
        self.modals = modals if modals else []
        
        # Delayed import to avoid circular dependencies if FocusManager is in another file
        from .manager import FocusManager
        self.fm = FocusManager(root_node, modals=self.modals)
        
        self.key_handler = key_handler # Can be a dict: {"q": quit_func}
        self.running = True
        self._last_key = None
        self.fps_limit = 1/60 

    @contextmanager
    def _raw_mode(self):
        """Standard raw mode setup for terminal input."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            yield
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def get_input(self):
        """Reads input while preventing partial escape sequence leaks."""
        fd = sys.stdin.fileno()
        r, _, _ = select.select([fd], [], [], 0)
        if not r:
            return None
        
        try:
            char = os.read(fd, 1).decode('utf-8', errors='ignore')
            # Check for escape sequences (Arrows: \x1b[A, etc.)
            if char == '\x1b':
                r_seq, _, _ = select.select([fd], [], [], 0.02)
                if r_seq:
                    char += os.read(fd, 5).decode('utf-8', errors='ignore')
            return char
        except Exception:
            return None

    def handle_input(self, key):
        """Priority-based input routing."""
        # Check if the currently focused node is an input field (reactive)
        focused = self.fm.current
        is_typing = getattr(focused, "is_reactive", False)

        # 1. Hardcoded Global: Emergency Exit
        if key == '\x03': # Ctrl+C
            self.stop()
            return

        # 2. Global '?' for Help
        # Only triggers if NOT inside a textbox/reactive node
        if key == '?' and not is_typing:
            self.show_help()
            return

        # 3. Custom Key Handler (App-level overrides)
        if self.key_handler and not is_typing:
            if isinstance(self.key_handler, dict) and key in self.key_handler:
                self.key_handler[key]()
                return
            elif hasattr(self.key_handler, "handle_key"):
                if self.key_handler.handle_key(key):
                    return

        # 4. UI Component Handler (FocusManager)
        self.fm.handle_input(key)

    def show_help(self):
        """Logic to display help. You can trigger a modal here."""
        # Example: if you have a help modal in self.modals:
        # self.modals[0].is_active = True
        pass

    def stop(self):
        self.running = False

    def run(self):
        """The Main Rendering & Input Loop."""
        with self._raw_mode():
            # Hide cursor (\x1b[?25l) and Clear Screen (\x1b[2J)
            sys.stdout.write("\x1b[?25l\x1b[2J")
            sys.stdout.flush()
            
            try:
                while self.running:
                    start_time = time.perf_counter()

                    # 1. Terminal Size
                    try:
                        cols, rows = os.get_terminal_size()
                    except OSError:
                        cols, rows = 80, 24
                    
                    # 2. Render Hierarchy
                    buffer = self.root.display(cols, rows)
                    for modal in self.modals:
                        if getattr(modal, "is_active", False):
                            buffer = modal.display_over(buffer, cols, rows)
                    
                    # 3. Flicker-free Flush
                    # \x1b[H = Cursor to Home. \r\n = Proper line breaks in raw mode.
                    sys.stdout.write("\x1b[H" + "\r\n".join(buffer))
                    sys.stdout.flush()
                    
                    # 4. Input Processing
                    key = self.get_input()
                    if key:
                        self._last_key = key
                        self.handle_input(key)
                
                    # 5. Precise FPS Cap
                    elapsed = time.perf_counter() - start_time
                    sleep_time = self.fps_limit - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                        
            except KeyboardInterrupt:
                pass
            finally:
                # Cleanup: Show cursor, reset colors, move to bottom
                sys.stdout.write("\x1b[?25h\x1b[0m\r\n")
                sys.stdout.flush()

    @property
    def last_key(self):
        return self._last_key