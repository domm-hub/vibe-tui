import os
import sys
import time
import termios
import tty
import select
from contextlib import contextmanager
from ..node import Node
from .manager import FocusManager
import ctypes

# load the C++ opt.so for row merging
here = os.path.dirname(__file__)
opt_path = os.path.join(here, "opt.so")
lib = ctypes.CDLL(opt_path)
_merge_rows = lib.merge_rows
_merge_rows.argtypes = [
    ctypes.POINTER(ctypes.c_char_p),
    ctypes.POINTER(ctypes.c_char_p),
    ctypes.POINTER(ctypes.c_char_p),
    ctypes.c_int
]


class EApp:
    def __init__(self, root_node, modals=None, key_handler=None, static_root=None, width=None, height=None, target_fps=60):
        try:
            cols, rows = os.get_terminal_size()
        except Exception:
            cols, rows = 240, 50

        self.width = width or cols
        self.height = height or rows
        self.static_root = static_root if static_root else Node()
        self.ui_root = root_node
        self.modals = modals if modals else []
        self.key_handler = key_handler

        # pre-allocate row buffers
        self.static_lines = [bytearray(b" " * self.width) for _ in range(self.height)]
        self.ui_lines = [None for _ in range(self.height)]
        self.prev_rows = [bytearray(b" " * self.width) for _ in range(self.height)]

        self.fm = FocusManager(self.ui_root, modals=self.modals)
        self.target_fps = target_fps
        self.fps_limit = 1.0 / target_fps
        self.running = True
        self.dirty_static = True
        self._last_key = None
        self.logic_time = 0
        self.render_time = 0
        self.actual_fps = 0

    def _ensure_grid_size(self):
        try:
            cols, rows = os.get_terminal_size()
        except Exception:
            cols, rows = self.width, self.height

        if self.width != cols or self.height != rows:
            self.width = cols
            self.height = rows
            self.static_lines = [bytearray(b" " * self.width) for _ in range(self.height)]
            self.ui_lines = [None for _ in range(self.height)]
            self.prev_rows = [bytearray(b" " * self.width) for _ in range(self.height)]
            self.dirty_static = True

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
        if not r:
            return None
        try:
            char = os.read(fd, 6).decode('utf-8', errors='ignore')
            return char
        except Exception:
            return None

    def handle_input(self, key):
        focused = self.fm.current
        is_typing = getattr(focused, "is_reactive", False)

        if key == '\x03':  # Ctrl+C
            self.stop()
            return

        if self.key_handler and not is_typing:
            if isinstance(self.key_handler, dict) and key in self.key_handler:
                self.key_handler[key]()
                return

        self.fm.handle_input(key)

    def stop(self):
        self.running = False

    def _merge_to_rows(self):
        """Use C++ merging + preallocated buffers for max speed"""
        # convert Python lists to ctypes arrays
        s_lines = (ctypes.c_char_p * self.height)(*map(lambda b: bytes(b), self.static_lines))
        u_lines = (ctypes.c_char_p * self.height)(*map(lambda b: bytes(b) if b else b"", self.ui_lines))
        out_rows = (ctypes.c_char_p * self.height)()
        _merge_rows(s_lines, u_lines, out_rows, self.height)
        # update prev_rows in place, reuse buffers
        for i in range(self.height):
            self.prev_rows[i][:] = out_rows[i]
        return out_rows

    def run(self):
        from .. import statements
        from .. import UILabel

        target_fps = statements.config.get("fps", 60)
        self.fps_limit = 1 / target_fps
        sleep_multiplier = 0.98

        prev_time = time.perf_counter()
        last_stats_update = prev_time
        frame_times = []
        fps_count = UILabel(2, "-- stats")

        if statements.config.get("fps_counter", False):
            if hasattr(self.ui_root, "add"):
                self.ui_root.add(fps_count)

        with self._raw_mode():
            sys.stdout.write("\x1b[?25l\x1b[2J")  # Hide cursor, Clear screen
            sys.stdout.flush()

            try:
                while self.running:
                    start_tick = time.perf_counter()
                    self._ensure_grid_size()

                    # 1. LOGIC PHASE
                    if self.dirty_static:
                        static_out = self.static_root.display(self.width, self.height)
                        for i, line in enumerate(static_out):
                            self.static_lines[i][:] = line.encode()
                        self.dirty_static = False

                    ui_out = self.ui_root.display(self.width, self.height)
                    for i, line in enumerate(ui_out):
                        self.ui_lines[i] = line.encode() if line else None

                    current_rows = self._merge_to_rows()

                    # apply modals
                    for modal in self.modals:
                        if getattr(modal, "is_active", False) and hasattr(modal, "display_over"):
                            current_rows = modal.display_over(current_rows, self.width, self.height)

                    self.logic_time = (time.perf_counter() - start_tick) * 1000

                    # 2. RENDER PHASE (Batch flush)
                    render_start = time.perf_counter()
                    output_bytes = bytearray()
                    for r, row in enumerate(current_rows):
                        if row != self.prev_rows[r]:
                            output_bytes.extend(b"\x1b[" + str(r + 1).encode() + b";1H" + row)
                            self.prev_rows[r][:] = row
                    if output_bytes:
                        sys.stdout.buffer.write(output_bytes)
                        sys.stdout.flush()

                    self.render_time = (time.perf_counter() - render_start) * 1000

                    # 3. INPUT PHASE
                    key = self.get_input()
                    if key:
                        self._last_key = key
                        self.handle_input(key)

                    # 4. FPS CONTROL
                    execution_time = time.perf_counter() - start_tick
                    time_left = self.fps_limit - execution_time
                    if time_left > 0:
                        time.sleep(time_left * sleep_multiplier)

                    total_frame_time = time.perf_counter() - start_tick
                    if total_frame_time > self.fps_limit:
                        sleep_multiplier = max(0.90, sleep_multiplier - 0.001)
                    else:
                        sleep_multiplier = min(0.99, sleep_multiplier + 0.001)

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

    def set_static_dirty(self):
        self.dirty_static = True