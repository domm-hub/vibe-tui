from ..keyinput import Key
from ..event.eventmanager import Event

class FocusManager:
    def __init__(self, root_node):
        self.root = root_node
        self.focusable_nodes = []
        self.index = 0
        self.refresh_nodes()

    def refresh_nodes(self):
        """Deep-scans tree and keeps focus locked to the current object reference."""
        current_node = self.focusable_nodes[self.index] if self.focusable_nodes and self.index < len(self.focusable_nodes) else None
        
        self.focusable_nodes = self._find_focusable(self.root)
        
        if self.focusable_nodes:
            # Re-map index to the same object so focus doesn't jump
            if current_node in self.focusable_nodes:
                self.index = self.focusable_nodes.index(current_node)
            else:
                self.index = min(self.index, len(self.focusable_nodes) - 1)
                
            for i, node in enumerate(self.focusable_nodes):
                node.selected = (i == self.index)

    def _find_focusable(self, node):
        """
        Fixed Recursion: Strictly separates Layout nodes from Tab content 
        to ensure every widget is only found ONCE.
        """
        focusable = []
        
        # 1. Self-Check
        if getattr(node, 'focusable', True):
            focusable.append(node)
            
        # 2. Layout Discovery (HL/VL)
        # We use a set to keep track of what we've already found in this branch
        found_ids = set()

        if hasattr(node, 'nodes'):
            for child in node.nodes:
                child_nodes = self._find_focusable(child)
                for cn in child_nodes:
                    if id(cn) not in found_ids:
                        focusable.append(cn)
                        found_ids.add(id(cn))
        
        # 3. Tab Content Discovery
        # If it's a TabManager, only dive into the ACTIVE content body,
        # ignore the buttons because they were already found in step 2.
        if hasattr(node, 'get_active_content'):
            content = node.get_active_content()
            if content:
                content_nodes = self._find_focusable(content)
                for cn in content_nodes:
                    if id(cn) not in found_ids:
                        focusable.append(cn)
                        found_ids.add(id(cn))

        return focusable

    def next(self):
        if not self.focusable_nodes: return
        # Atomic swap: remove old, add new
        self.focusable_nodes[self.index].selected = False
        self.index = (self.index + 1) % len(self.focusable_nodes)
        self.focusable_nodes[self.index].selected = True

    def prev(self):
        if not self.focusable_nodes: return
        self.focusable_nodes[self.index].selected = False
        self.index = (self.index - 1) % len(self.focusable_nodes)
        self.focusable_nodes[self.index].selected = True

    @property
    def current(self):
        return self.focusable_nodes[self.index] if self.focusable_nodes else None

    def handle_input(self, key):
        event = Event(key)
        if event.is_tab:
            self.next()
        elif event.is_btab:
            self.prev()
        elif self.current:
            if hasattr(self.current, 'handle_input'):
                self.current.handle_input(key)
                # If the widget is a TabManager, switching tabs changes the focusable tree
                if hasattr(self.current, 'get_active_content'):
                    self.refresh_nodes()
            elif event.is_enter or (event.is_char and event.char == " "):
                if hasattr(self.current, 'press'):
                    self.current.press()
                    self.refresh_nodes()