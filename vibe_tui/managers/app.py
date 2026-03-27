import os
import sys
import time
import select
import termios
import tty
from contextlib import contextmanager
from .. import statements
import ctypes
import os

# 1. Get the directory where THIS script (EApp.py) is located
# Use os.path.realpath to follow any symlinks automatically
BASE_DIR = os.path.dirname(os.path.realpath(__file__))

# 2. Join it with your filename
# This works even if you run "python3 TUI/main.py" from your home folder
lib_path = os.path.join(BASE_DIR, "join.so")

lib = ctypes.CDLL(os.path.abspath(lib_path))

# 2. Tell Python: "fast_join_rows" takes a (char**) and an (int)
# In ctypes, char** is represented as a POINTER to a c_char_p
lib.fast_join_rows.argtypes = [ctypes.POINTER(ctypes.c_char_p), ctypes.c_int]

# 3. Tell Python: It returns a raw C-string (char*)
lib.fast_join_rows.restype = ctypes.c_char_p

def render(rows):
    height = len(rows)
    
    # 1. Convert Python strings to bytes (C++ loves bytes, not Unicode)
    # 2. Create a "C-Style Array" of char pointers
    # This line IS the definition of c_array
    c_array = (ctypes.c_char_p * height)(*[row.encode('utf-8') for row in rows])
    
    # 3. Now you pass that c_array to the C++ function
    return lib.fast_join_rows(c_array, height).decode('utf-8')

class App:
    def __init__(self, root_node, modals=None, key_handler=None):
        self.root = root_node
        self.modals = modals if modals else []
        from .manager import FocusManager
        self.fm = FocusManager(root_node, modals=self.modals)
        self.key_handler = key_handler
        self.running = True
        self._last_key = None
        self.fps_limit = 1/statements.config.get("fps", 60)

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
        """Standard engine loop with Precision Adaptive Sleep."""
        from .. import UILabel
        
        target_fps = statements.config.get("fps", 60)
        self.fps_limit = 1 / target_fps
        
        # Adaptive sleep parameters
        sleep_multiplier = 0.98
        
        prev_time = time.perf_counter()
        last_stats_update = prev_time
        fps_count = UILabel(2, "-- stats")
        
        # Statistics tracking
        frame_times = []
        
        if statements.config.get("fps_counter", False):
            self.root.add(fps_count)
            
        with self._raw_mode():
            sys.stdout.write("\x1b[?25l\x1b[2J")
            sys.stdout.flush()
            try:
                while self.running:
                    # 1. Start Frame Timer
                    start_tick = time.perf_counter()
                    
                    # 2. Execution (Rendering & Logic)
                    cols, rows = os.get_terminal_size()
                    buffer = self.root.display(cols, rows)
                    
                    for modal in self.modals:
                        if getattr(modal, "is_active", False):
                            buffer = modal.display_over(buffer, cols, rows)
                    
                    sys.stdout.write("\x1b[H" + render(buffer))
                    sys.stdout.flush()
                    
                    # Input handling
                    key = self.get_input()
                    if key:
                        self._last_key = key
                        self.handle_input(key)
                    
                    # 3. Precision Sleep & Spin-wait
                    execution_time = time.perf_counter() - start_tick
                    time_left = self.fps_limit - execution_time
                    
                    if time_left > 0:
                        # Adaptive Sleep
                        time.sleep(time_left * sleep_multiplier)
                        # Precision Spin-wait to hit exact budget
                        while time.perf_counter() - start_tick < self.fps_limit:
                            pass
                
                    total_frame_time = time.perf_counter() - start_tick
                    
                    # 4. Adaptive Adjustment
                    if total_frame_time > self.fps_limit:
                        sleep_multiplier = max(0.90, sleep_multiplier - 0.001)
                    else:
                        sleep_multiplier = min(0.99, sleep_multiplier + 0.001)

                    # 5. Stats Calculation (Update every 0.1s)
                    current_time = time.perf_counter()
                    delta_time = current_time - prev_time
                    prev_time = current_time
                    
                    if delta_time > 0:
                        frame_times.append(delta_time)
                        if len(frame_times) > target_fps:
                            frame_times.pop(0)
                        
                        if current_time - last_stats_update >= 0.1:
                            avg_fps = len(frame_times) / sum(frame_times)
                            actual_fps = 1 / delta_time
                            
                            stats = (
                                f"FPS: {int(actual_fps)} (Avg: {int(avg_fps)}) | "
                                f"Exec: {execution_time*1000:.2f}ms | "
                                f"Mult: {sleep_multiplier:.3f}"
                            )
                            fps_count.set_text(stats)
                            last_stats_update = current_time
            finally:
                sys.stdout.write("\x1b[?25h\x1b[0m\r\n")
                sys.stdout.flush()