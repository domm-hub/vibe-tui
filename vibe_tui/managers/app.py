import os
import sys
import time
import select
import termios
import tty
from contextlib import contextmanager

class VibeApp:
    def __init__(self, root_node, modals=None, key_handler=None):
        self.root = root_node
        self.modals = modals if modals else []
        from .manager import FocusManager
        self.fm = FocusManager(root_node, modals=self.modals)
        self.key_handler = key_handler
        self.running = True
        self._last_key = None
        self.fps_limit = 1/60 

    @contextmanager
    def _raw_mode(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            yield
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def get_input(self):
        fd = sys.stdin.fileno()
        r, _, _ = select.select([fd], [], [], 0)
        if not r: return None
        try:
            char = os.read(fd, 1).decode('utf-8', errors='ignore')
            if char == '\x1b':
                r_seq, _, _ = select.select([fd], [], [], 0.02)
                if r_seq:
                    char += os.read(fd, 5).decode('utf-8', errors='ignore')
            return char
        except Exception: return None

    def handle_input(self, key):
        focused = self.fm.current
        is_typing = getattr(focused, "is_reactive", False)

        if key == '\x03': # Ctrl+C
            self.stop()
            return

        if self.key_handler and not is_typing:
            if isinstance(self.key_handler, dict) and key in self.key_handler:
                self.key_handler[key]()
                return

        self.fm.handle_input(key)

    def stop(self):
        self.running = False

    def run(self):
        """Standard engine loop."""
        with self._raw_mode():
            sys.stdout.write("\x1b[?25l\x1b[2J")
            sys.stdout.flush()
            try:
                while self.running:
                    start_time = time.perf_counter()
                    cols, rows = os.get_terminal_size()
                    
                    buffer = self.root.display(cols, rows)
                    for modal in self.modals:
                        if getattr(modal, "is_active", False):
                            buffer = modal.display_over(buffer, cols, rows)
                    
                    sys.stdout.write("\x1b[H" + "\r\n".join(buffer))
                    sys.stdout.flush()
                    
                    key = self.get_input()
                    if key:
                        self._last_key = key
                        self.handle_input(key)
                
                    elapsed = time.perf_counter() - start_time
                    sleep_time = self.fps_limit - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
            finally:
                sys.stdout.write("\x1b[?25h\x1b[0m\r\n")
                sys.stdout.flush()