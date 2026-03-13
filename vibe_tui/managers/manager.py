class FocusManager:
    def __init__(self, items):
        """
        Manages TAB selection across multiple layouts or individual nodes.
        
        Args:
            items (list): A list containing Nodes, UIContainers, or a mix of both.
        """
        self.focusable_nodes = []
        self.current_index = 0
        
        # 1. Extract all interactive nodes from the provided items
        for item in items:
            self._extract_focusable(item)
            
        # 2. Initialize the first node as selected (if any exist)
        if self.focusable_nodes:
            self.focusable_nodes[self.current_index].selected = True
            
    def _extract_focusable(self, node):
        """
        Recursively searches containers to find interactive leaf nodes.
        """
        # If the node is a Container, search its children
        if hasattr(node, 'nodes') and isinstance(node.nodes, list):
            for child in node.nodes:
                self._extract_focusable(child)
                
        # If it's a leaf node, check if it's meant to be interactive.
        # We assume nodes with an 'handle_input', 'press', or specific types are focusable.
        # You can adjust this condition based on your specific node classes.
        elif hasattr(node, 'selected'):
             # Optional: Add a check here if you have read-only UIBoxes that shouldn't be focused
             # e.g., if not getattr(node, 'is_readonly', False):
             self.focusable_nodes.append(node)

    def next_focus(self):
        """
        Cycles focus to the NEXT interactive node (simulates pressing TAB).
        """
        if not self.focusable_nodes:
            return

        # Deselect current
        self.focusable_nodes[self.current_index].selected = False
        
        # Move index forward, wrapping around to 0 if at the end
        self.current_index = (self.current_index + 1) % len(self.focusable_nodes)
        
        # Select new
        self.focusable_nodes[self.current_index].selected = True

    def prev_focus(self):
        """
        Cycles focus to the PREVIOUS interactive node (simulates Shift+TAB).
        """
        if not self.focusable_nodes:
            return

        # Deselect current
        self.focusable_nodes[self.current_index].selected = False
        
        # Move index backward, wrapping around to the end if at 0
        self.current_index = (self.current_index - 1) % len(self.focusable_nodes)
        
        # Select new
        self.focusable_nodes[self.current_index].selected = True

    def get_active_node(self):
        """
        Returns the currently focused node so you can pass it keystrokes.
        """
        if not self.focusable_nodes:
            return None
        return self.focusable_nodes[self.current_index]
