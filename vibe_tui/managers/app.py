import os
import sys
import time
import select
import termios
import tty
import platform
import ctypes
from contextlib import contextmanager
from .. import statements

class App:
    _lib = None

    _warned = False

    @classmethod
    def get_lib(cls):
        if cls._lib is None:
            base_dir = os.path.dirname(os.path.realpath(__file__))
            
            # Try to find the library with various suffixes (to handle setuptools naming)
            lib_path = None
            ext = ".dll" if platform.system() == "Windows" else ".so"
            
            # 1. Try exact match
            p = os.path.join(base_dir, f"opt{ext}")
            if os.path.exists(p):
                lib_path = p
            else:
                # 2. Try matching with glob (for something like opt.cpython-312-darwin.so)
                import glob
                matches = glob.glob(os.path.join(base_dir, f"opt*{ext}"))
                if matches:
                    lib_path = matches[0]

            if not lib_path:
                if not cls._warned:
                    print("WARNING: C++ extension 'opt' not found. Reverting to pure Python version.", file=sys.stderr)
                    cls._warned = True
                return None

            try:
                cls._lib = ctypes.CDLL(os.path.abspath(lib_path))
                cls._lib.fast_join_rows.argtypes = [ctypes.POINTER(ctypes.c_char_p), ctypes.c_int]
                cls._lib.fast_join_rows.restype = ctypes.c_char_p
            except Exception:
                if not cls._warned:
                    print("WARNING: Failed to load C++ extension 'opt'. Reverting to pure Python version.", file=sys.stderr)
                    cls._warned = True
                return None
        return cls._lib

    def __init__(self, root_node, modals=None, key_handler=None):
        self.root = root_node
        self.modals = modals if modals else []
        from .manager import FocusManager
        self.fm = FocusManager(root_node, modals=self.modals)
        self.key_handler = key_handler
        self.running = False
        
        # Load the C++ library once on instantiation
        App.get_lib()

    @contextmanager
    def _terminal_setup(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            # hide cursor
            sys.stdout.write("\033[?25l")
            sys.stdout.flush()
            yield
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            # show cursor
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()

    def _get_input(self):
        # check if there's input waiting on stdin
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
        return None

    def run(self, target_fps=60):
        self.running = True
        fps_limit = 1 / target_fps
        
        with self._terminal_setup():
            while self.running:
                loop_start = time.perf_counter()
                
                # input
                key = self._get_input()
                if key:
                    self._handle_input(key)
                
                # update
                
                # render
                x = os.get_terminal_size()
                rows = self.root.display(x.columns, x.lines)
                rendered_frame = render(rows)
                
                sys.stdout.write("\033[H" + rendered_frame)
                sys.stdout.flush()
                
                # FPS cap
                elapsed = time.perf_counter() - loop_start
                if elapsed < fps_limit:
                    time.sleep(fps_limit - elapsed)

    def _handle_input(self, key):
        if key == "\x1b": # ESC
            self.running = False
            return
            
        if self.key_handler:
            if callable(self.key_handler):
                self.key_handler(key)
                return
            if isinstance(self.key_handler, dict) and key in self.key_handler:
                self.key_handler[key]()
                return
        
        self.fm.handle_input(key)

    def stop(self):
        self.running = False

def render(rows):
    height = len(rows)
    lib = App.get_lib()
    
    if lib:
        # 1. Convert Python strings to bytes (C++ loves bytes, not Unicode)
        # 2. Create a "C-Style Array" of char pointers
        c_array = (ctypes.c_char_p * height)(*[row.encode('utf-8') for row in rows])
        
        # 3. Now you pass that c_array to the C++ function
        return lib.fast_join_rows(c_array, height).decode('utf-8')
    
    # Pure Python fallback:
    return "".join(rows)
