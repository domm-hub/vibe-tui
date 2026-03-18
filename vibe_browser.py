import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from vibe_tui import (
    VibeApp,
    UiContainerVertical,
    UiContainerHorizontal,
    UISelect,
    UIScrollText,
    UILabel,
    UIInput,
    UIEditor,
    UIModal,
    UIModalNode,
    UIToast,
    Colors,
    Theme,
    Key,
    TabManagerH,
    Tab,
    UITerminal
)
from vibe_tui.base.colors import LIGHT_BLUE_THEME

# Apply the global text theme
Theme.set_color_theme(LIGHT_BLUE_THEME)

class AdvancedFileBrowser:
    def __init__(self, start_path="."):
        self.current_path = Path(start_path).resolve()
        self.sort_by_name = True
        self.show_hidden = False
        self.clipboard = None
        self.editing_path = None
        
        # --- File Browser Tab ---
        self.tab_files = UiContainerVertical(weight=1)
        self.breadcrumbs = UILabel(weight=1, text="")
        self.search_bar = UIInput(weight=1, label="   SEARCH: ", initial_text="")
        
        file_main_layout = UiContainerHorizontal(weight=18)
        self.file_list = UISelect(weight=1, title=" FILES ")
        self.preview_text = UIScrollText(weight=2, title=" PREVIEW ", show_line_numbers=True, wrap=False)
        file_main_layout.add(self.file_list).add(self.preview_text)
        self.tab_files.add(self.breadcrumbs).add(self.search_bar).add(file_main_layout)

        # --- Terminal Tab ---
        self.terminal = UITerminal(weight=1, title=" SHELL ")

        # --- Main Layout ---
        self.root = UiContainerVertical(weight=1)
        self.header = UILabel(weight=1, text=f" {Colors.BOLD}{Colors.BLUE} VIBE ADVANCED NAVIGATOR {Colors.RESET}")
        
        self.tabs = TabManagerH([
            Tab("   Files ", self.tab_files),
            Tab("   Terminal ", self.terminal)
        ], weight=1)
        
        self.active_content_container = UiContainerVertical(weight=20)
        self.active_content_container.add(self.tab_files)
        
        self.footer = UILabel(weight=1, text="")
        self.root.add(self.header).add(self.tabs).add(self.active_content_container).add(self.footer)
        
        # Tab Switching Logic
        def on_tab_change(idx):
            self.active_content_container.reset()
            self.active_content_container.add(self.tabs.get_active_content())
            # Refresh focus to the new tab's elements
            self.app.fm.refresh_nodes()
            
        self.tabs.on("change", on_tab_change)

        # Modals & Overlays
        self.help_modal = UIModal(width_pct=0.6, height_pct=0.7, title="[ HELP ]", 
                                  text=f"{Colors.BOLD}Shortcuts{Colors.RESET}\n\n"
                                       "Arrows/Enter : Navigate\n"
                                       "Backspace    : Go up\n"
                                       "Tab          : Switch panels / Tabs\n"
                                       "y / p        : Yank (Copy) / Paste\n"
                                       "r / e        : Rename / Edit File\n"
                                       "n / N        : New File / New Folder\n"
                                       "d            : Delete item\n"
                                       "c / o        : Copy Path / Open VSCode\n"
                                       "s / .        : Toggle Sort / Hidden\n"
                                       "h / q        : Help / Quit")

        self.confirm_modal = UIModal(width_pct=0.4, height_pct=0.2, title="[ CONFIRM ]", text="")
        self.toast = UIToast(duration=2)
        
        # Input Modals
        self.input_field = UIInput(weight=1, label=" Name: ", initial_text="")
        self.input_modal = UIModalNode(self.input_field, width_pct=0.4, height_pct=0.2, title="[ INPUT ]")

        # Editor Modal
        self.editor_field = UIEditor(weight=1, text="", title=" FILE EDITOR (Ctrl+S to save) ")
        self.editor_modal = UIModalNode(self.editor_field, width_pct=0.8, height_pct=0.8, title="[ EDITOR ]")

        self.root.add(self.header).add(self.breadcrumbs).add(self.search_bar).add(main_layout).add(self.footer)

        # 2. Application Logic
        self.all_items = []
        self.current_filtered_items = []
        self.load_directory(self.current_path)
        
        self.file_list.on("change", self.on_file_selected)
        self.search_bar.on("change", lambda q: self.apply_filter(q))

        # 3. Initialize VibeApp Engine
        self.app = VibeApp(self.root, modals=[self.help_modal, self.confirm_modal, self.input_modal, self.editor_modal, self.toast])

    def update_ui_state(self):
        parts = list(self.current_path.parts)
        if len(parts) > 6: parts = ["..."] + parts[-5:]
        self.breadcrumbs.set_text(f" {Colors.CYAN}󱡁 {' ❯ '.join(parts)}{Colors.RESET}")
        
        last_key = repr(self.app.last_key) if hasattr(self, 'app') else "'None'"
        clipboard_status = f"{Colors.GREEN}[ Yanked ]{Colors.RESET}" if self.clipboard else ""
        self.footer.set_text(f" {Colors.MAGENTA}  {last_key}{Colors.RESET} | {Colors.CYAN}h: Help | y/p: Yank/Paste{Colors.RESET} {clipboard_status}")

    def load_directory(self, path):
        self.current_path = Path(path).resolve()
        try:
            items = list(os.scandir(self.current_path))
            if not self.show_hidden:
                items = [e for e in items if not e.name.startswith('.')]
                
            key_func = lambda e: (not e.is_dir(), e.name.lower()) if self.sort_by_name else (not e.is_dir(), e.stat().st_size if e.is_file() else 0)
            items.sort(key=key_func, reverse=not self.sort_by_name)
            
            self.all_items = []
            for entry in items:
                name = entry.name
                is_dir = entry.is_dir()
                if is_dir: icon, color = " ", Colors.BLUE
                elif name.endswith(('.py', '.js', '.ts')): icon, color = " ", Colors.GREEN
                elif name.endswith(('.png', '.jpg', '.svg', '.jpeg')): icon, color = " ", Colors.MAGENTA
                elif name.endswith(('.md', '.txt')): icon, color = " ", Colors.CYAN
                else: icon, color = "  ", ""
                self.all_items.append((f"{color}{icon} {name}{'/' if is_dir else ''}{Colors.RESET}", name, is_dir))
            
            self.apply_filter(self.search_bar.text)
            self.update_ui_state()
        except PermissionError:
            self.file_list.options = [f"{Colors.RED}Permission Denied{Colors.RESET}"]

    def apply_filter(self, query):
        if not query: 
            filtered = self.all_items
        else: 
            filtered = [item for item in self.all_items if query.lower() in item[1].lower()]
            
        self.file_list.options = [item[0] for item in filtered]
        self.current_filtered_items = filtered
        if self.file_list.selection >= len(filtered): self.file_list.selection = max(0, len(filtered) - 1)
        if filtered: self.on_file_selected(None)
        else: self.preview_text.set_text("No matches found.")

    def is_binary(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                return b'\0' in f.read(1024)
        except: return False

    def on_file_selected(self, _):
        if not self.current_filtered_items: return
        _, raw_name, is_dir = self.current_filtered_items[self.file_list.selection]
        full_path = self.current_path / raw_name
        
        if is_dir:
            try:
                all_sub = list(os.scandir(full_path))
                content = sorted(all_sub, key=lambda e: e.name)[:15]
                preview = f"Folder: {Colors.BOLD}{raw_name}{Colors.RESET}\nItems: {len(all_sub)}\n\nContents:\n"
                preview += "\n".join([f" {' ' if e.is_dir() else '  '} {e.name}" for e in content])
                self.preview_text.set_text(preview)
            except: self.preview_text.set_text("Permission Denied")
        else:
            try:
                stats = full_path.stat()
                info = f"File: {Colors.BOLD}{raw_name}{Colors.RESET}\nSize: {self.format_size(stats.st_size)}\nModified: {datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}\n{'-'*40}\n"
                
                ext = raw_name.lower().split('.')[-1]
                if self.is_binary(full_path) and ext not in ('png', 'jpg', 'jpeg', 'svg', 'webp', 'bmp'):
                    self.preview_text.set_text(info + f"{Colors.YELLOW}< Binary File - Preview Disabled >{Colors.RESET}")
                elif ext in ('png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp'):
                    from vibe_tui.base.basic import get_image_box
                    cols, rows = os.get_terminal_size()
                    img_block = get_image_box(str(full_path), w=int((2/3)*cols)-4, h=rows-8, chars=Theme.NONE)
                    self.preview_text.set_text("\n".join(img_block))
                elif ext in ('py', 'js', 'ts', 'c', 'cpp', 'rs', 'go', 'html', 'css', 'json', 'yaml', 'toml', 'sh', 'md'):
                    try:
                        from rich.console import Console
                        from rich.syntax import Syntax
                        from rich.markdown import Markdown
                        import io
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f: code_content = f.read(10000)
                        cols, _ = os.get_terminal_size()
                        string_io = io.StringIO()
                        console = Console(file=string_io, force_terminal=True, width=max(40, int((2/3)*cols)-4))
                        if ext == 'md': console.print(Markdown(code_content))
                        else: console.print(Syntax(code_content, ext if ext != 'py' else 'python', theme="monokai", line_numbers=False))
                        self.preview_text.set_text(info + string_io.getvalue())
                    except:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f: self.preview_text.set_text(info + f.read(5000))
                else:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f: self.preview_text.set_text(info + f.read(5000))
            except Exception as e: self.preview_text.set_text(f"Error: {e}")

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024: return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def copy_path(self):
        if not self.current_filtered_items: return
        _, raw_name, _ = self.current_filtered_items[self.file_list.selection]
        full_path = str((self.current_path / raw_name).resolve())
        try:
            if sys.platform == 'darwin': subprocess.run(['pbcopy'], input=full_path.encode('utf-8'), check=True)
            elif sys.platform == 'linux': subprocess.run(['xclip', '-selection', 'clipboard'], input=full_path.encode('utf-8'), check=True)
            self.toast.show("Path copied to clipboard")
        except: self.toast.show("Could not access clipboard")

    def yank(self):
        if not self.current_filtered_items: return
        _, raw_name, _ = self.current_filtered_items[self.file_list.selection]
        self.clipboard = self.current_path / raw_name
        self.toast.show(f"Yanked: {raw_name}")

    def paste(self):
        if not self.clipboard: return self.toast.show("Clipboard is empty")
        dst = self.current_path / self.clipboard.name
        if dst.exists(): return self.toast.show("File already exists!")
        try:
            if self.clipboard.is_dir(): shutil.copytree(self.clipboard, dst)
            else: shutil.copy2(self.clipboard, dst)
            self.load_directory(self.current_path)
            self.toast.show(f"Pasted {self.clipboard.name}")
        except Exception as e: self.toast.show(f"Error: {e}")

    def delete_item(self):
        if not self.current_filtered_items: return
        _, raw_name, is_dir = self.current_filtered_items[self.file_list.selection]
        full_path = self.current_path / raw_name
        def do_delete():
            try:
                if is_dir: shutil.rmtree(full_path)
                else: os.remove(full_path)
                self.load_directory(self.current_path)
                self.toast.show(f"Deleted {raw_name}")
            except Exception as e: self.toast.show(f"Error: {e}")
            self.confirm_modal.is_active = False
            self.confirm_modal._subscribers.pop("confirm", None)
        self.confirm_modal.text = f"DELETE {raw_name}?\n\n[ Enter: YES | ESC: NO ]"
        self.confirm_modal.is_active = True
        self.confirm_modal.on("confirm", do_delete)

    def prompt_input(self, title, callback, initial=""):
        self.input_modal.title = f"[ {title} ]"
        self.input_field.set_text(initial)
        self.input_modal.is_active = True
        def handle_submit():
            callback(self.input_field.text)
            self.input_modal.is_active = False
            self.input_modal._subscribers.pop("submit", None)
        self.input_modal.on("submit", handle_submit)

    def edit_file(self):
        if not self.current_filtered_items: return
        _, raw_name, is_dir = self.current_filtered_items[self.file_list.selection]
        if is_dir:
            self.toast.show("Cannot edit a directory")
            return
            
        full_path = self.current_path / raw_name
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editing_path = full_path
            self.editor_modal.title = f"[ EDITING: {raw_name} | ESC to close | Ctrl+S to save ]"
            self.editor_field.lines = content.splitlines() if content else [""]
            self.editor_field.cursor_x = 0
            self.editor_field.cursor_y = 0
            self.editor_modal.is_active = True
        except Exception as e:
            self.toast.show(f"Cannot open file: {e}")

    def save_file(self):
        if not self.editing_path: return
        try:
            content = "\n".join(self.editor_field.lines)
            with open(self.editing_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.toast.show(f"Saved {self.editing_path.name}")
            # Refresh preview if it's currently selected
            self.on_file_selected(None) 
        except Exception as e:
            self.toast.show(f"Save failed: {e}")

    def run(self):
        def custom_input_handler(key):
            # Editor Modal Input
            if self.editor_modal.is_active:
                if key == Key.ESCAPE[0]:
                    self.editor_modal.is_active = False
                    self.editing_path = None
                    return True
                elif key == '\x13': # Ctrl+S
                    self.save_file()
                    return True
                # Let the editor handle standard typing, arrows, etc.
                self.editor_field.handle_input(key)
                return True
                
            if self.input_modal.is_active:
                if key in (Key.ENTER[0], "\n"): self.input_modal.emit("submit"); return True
                if key == Key.ESCAPE[0]: self.input_modal.is_active = False; return True
                return False
            if self.confirm_modal.is_active:
                if key in (Key.ENTER[0], "\n"): self.confirm_modal.emit("confirm"); return True
                if key == Key.ESCAPE[0]: self.confirm_modal.is_active = False; return True
                return True
            if self.help_modal.is_active:
                if key in (Key.ESCAPE[0], 'q', ' ', 'h'): self.help_modal.is_active = False; return True
                return True
            if isinstance(self.app.fm.current, UIInput):
                return
            if key == 'h': self.help_modal.is_active = True; return True
            if key == 's': self.sort_by_name = not self.sort_by_name; self.load_directory(self.current_path); return True
            if key == '.': self.show_hidden = not self.show_hidden; self.load_directory(self.current_path); return True
            if key == 'c': self.copy_path(); return True
            if key == 'y': self.yank(); return True
            if key == 'p': self.paste(); return True
            if key == 'd': self.delete_item(); return True
            if key == 'e': self.edit_file(); return True
            if key == 'r':
                _, name, _ = self.current_filtered_items[self.file_list.selection]
                self.prompt_input("RENAME", lambda n: (os.rename(self.current_path/name, self.current_path/n), self.load_directory(self.current_path)), name)
                return True
            if key == 'n': self.prompt_input("NEW FILE", lambda n: ((self.current_path/n).touch(), self.load_directory(self.current_path))); return True
            if key == 'N': self.prompt_input("NEW FOLDER", lambda n: (os.mkdir(self.current_path/n), self.load_directory(self.current_path))); return True
            if key == 'o':
                _, name, _ = self.current_filtered_items[self.file_list.selection]
                try: subprocess.run(['code', str(self.current_path/name)], check=True); self.toast.show(f"Opened {name} in Code")
                except: self.toast.show("VS Code command 'code' not found")
                return True
            if key == 'q': self.app.stop(); return True
            if key in (Key.ENTER[0], "\n"):
                if self.app.fm.current == self.file_list:
                    _, raw_name, is_dir = self.current_filtered_items[self.file_list.selection]
                    if is_dir: self.load_directory(self.current_path / raw_name); self.search_bar.set_text("")
                    return True
            if key == Key.BACKSPACE[0] and self.app.fm.current != self.search_bar: self.go_up(); return True
            return False

        original_handle = self.app.fm.handle_input
        def wrap_handle(key):
            if not custom_input_handler(key): original_handle(key)
            self.update_ui_state()
        self.app.fm.handle_input = wrap_handle
        self.app.run()

    def go_up(self):
        if self.current_path.parent != self.current_path: self.load_directory(self.current_path.parent); self.search_bar.set_text("")

if __name__ == "__main__":
    AdvancedFileBrowser().run()
