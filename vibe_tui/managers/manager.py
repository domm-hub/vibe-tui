class FocusManager:
    def __init__(self, root_node):
        self.root = root_node
        self.focusable_nodes = []
        self.index = 0
        self.refresh_nodes()

    def refresh_nodes(self):
        """
        Deep-scans the UI tree to find everything that has focusable=True.
        Run this if you dynamically add/remove tabs or nodes.
        """
        self.focusable_nodes = self._find_focusable(self.root)
        if self.focusable_nodes:
            # Ensure only the currently indexed node is 'selected'
            for i, node in enumerate(self.focusable_nodes):
                node.selected = (i == self.index)

    def _find_focusable(self, node):
        """Recursive helper to walk the HL/VL tree."""
        focusable = []
        
        # If the node itself is focusable, add it
        if getattr(node, 'focusable', False):
            focusable.append(node)
            
        # If it's a container, look at its children
        if hasattr(node, 'children'):
            for child in node.children:
                focusable.extend(self._find_focusable(child))
        return focusable

    def next(self):
        """Cycles focus to the next element."""
        if not self.focusable_nodes: return
        
        self.focusable_nodes[self.index].selected = False
        self.index = (self.index + 1) % len(self.focusable_nodes)
        self.focusable_nodes[self.index].selected = True

    def prev(self):
        """Cycles focus to the previous element."""
        if not self.focusable_nodes: return
        
        self.focusable_nodes[self.index].selected = False
        self.index = (self.index - 1) % len(self.focusable_nodes)
        self.focusable_nodes[self.index].selected = True

    @property
    def current(self):
        """Returns the currently focused node."""
        if not self.focusable_nodes: return None
        return self.focusable_nodes[self.index]

    def handle_input(self, key):
        """
        The central brain of your app's interactivity.
        """
        # 1. Handle Global Navigation
        if key == "KEY_TAB":
            self.next()
        elif key == "KEY_BTAB": # Shift + Tab
            self.prev()
        
        # 2. Route input to the active widget
        elif self.current:
            # Check if the widget has a specific input handler (like UIInput or UISelect)
            if hasattr(self.current, 'handle_input'):
                self.current.handle_input(key)
            
            # Check for generic 'Press' actions (Buttons/Checkboxes)
            elif key == "KEY_ENTER" or key == " ":
                if hasattr(self.current, 'press'):
                    self.current.press()