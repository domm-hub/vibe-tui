import os
import sys
import shutil
import select
import termios
import tty
from ..keyinput import Key
from .manager import FocusManager

class VibeApp:
    def __init__(self, root_node, modals=None):
        """
        The Main Application Engine for Vibe-TUI.
        Handles the rendering loop, terminal state, and input routing.
        """
        self.root = root_node
        self.modals = modals if modals else []
        self.fm = FocusManager(root_node, modals=self.modals)
        self.running = True
        self._last_key = "None"

    def get_input(self):
        """Robustly reads a keypress or ANSI escape sequence from stdin."""
        try:
            from pytermgui import getch
            return getch()
        except ImportError:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                # Wait for input (blocking)
                r, _, _ = select.select([sys.stdin], [], [], None) 
                if not r: return None
                
                ch = sys.stdin.read(1)
                if ch == '\x1b':
                    # Start of an escape sequence - grab the rest
                    while True:
                        r, _, _ = select.select([sys.stdin], [], [], 0.05)
                        if r:
                            ch += sys.stdin.read(1)
                            if len(ch) > 10: break 
                        else:
                            break
                return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def stop(self):
        """Signals the application loop to terminate."""
        self.running = False

    def run(self):
        """Starts the main application loop."""
        try:
            # Hide cursor
            sys.stdout.write("\x1b[?25l")
            sys.stdout.flush()
            
            while self.running:
                # 1. Get terminal dimensions
                cols, rows = os.get_terminal_size()
                
                # 2. Render the main UI
                buffer = self.root.display(cols, rows)
                
                # 3. Overlay any active modals
                for modal in self.modals:
                    if getattr(modal, "is_active", False):
                        buffer = modal.display_over(buffer, cols, rows)
                
                # 4. Flush to terminal (Home cursor + buffer)
                sys.stdout.write("\x1b[H" + "\n".join(buffer))
                sys.stdout.flush()
                
                # 5. Handle Input
                key = self.get_input()
                if not key: continue
                
                self._last_key = key
                
                # Global Exit logic
                if key == '\x03': # Ctrl+C
                    break
                
                # Delegate to FocusManager
                self.fm.handle_input(key)
                
        except KeyboardInterrupt:
            pass
        finally:
            # Restore terminal: Show cursor, reset colors, clear screen
            sys.stdout.write("\x1b[?25h\x1b[0m\x1b[2J\x1b[H")
            sys.stdout.flush()

    @property
    def last_key(self):
        return self._last_key