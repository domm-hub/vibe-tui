from ..node import Node

class UiContainerHorizontal(Node):
    def __init__(self, weight=1):
        super().__init__(weight=weight)
        self.nodes = []
        self.focusable = False

    def add(self, node: Node):
        self.nodes.append(node)
        return self

    def set_vibe(self, **kwargs):
        """Sets multiple attributes and returns self for easy chaining."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self

    def display(self, width, height):
        if not self.nodes: return [" " * width for _ in range(height)]
        
        total_weight = sum(n.weight for n in self.nodes)
        used_width = 0
        all_child_outputs = []
        child_widths = []
        
        for i, node in enumerate(self.nodes):
            # Calculate width for this slice
            if i == len(self.nodes) - 1:
                node_w = width - used_width
            else:
                node_w = int((node.weight / total_weight) * width) if total_weight > 0 else width // len(self.nodes)
            
            # Get child lines and store them
            all_child_outputs.append(node.display(node_w, height))
            child_widths.append(node_w)
            used_width += node_w

        # STITCHING: Join line 0 of every child, then line 1, etc.
        combined_output = []
        for row_idx in range(height):
            row_parts = []
            for col_idx, child_lines in enumerate(all_child_outputs):
                if row_idx < len(child_lines):
                    row_parts.append(child_lines[row_idx])
                else:
                    # Pad with exact width if this child didn't return enough lines
                    row_parts.append(" " * child_widths[col_idx])
            combined_output.append("".join(row_parts))
            
        return combined_output
    
    def reset(self):
        self.nodes = []
        return self

class UiContainerVertical(Node):
    def __init__(self, weight=1):
        super().__init__(weight=weight)
        self.nodes = []
        self.focusable = False

    def add(self, node: Node):
        self.nodes.append(node)
        return self

    def set_vibe(self, **kwargs):
        """Sets multiple attributes and returns self for easy chaining."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self
    
    def display(self, width, height):
        if not self.nodes: return [" " * width for _ in range(height)]
        
        total_weight = sum(n.weight for n in self.nodes)
        used_height = 0
        combined_output = []
        
        for i, node in enumerate(self.nodes):
            # Calculate height for this slice
            if i == len(self.nodes) - 1:
                node_h = height - used_height
            else:
                node_h = int((node.weight / total_weight) * height) if total_weight > 0 else height // len(self.nodes)
            
            # STACKING: Just extend the list with child lines
            combined_output.extend(node.display(width, node_h))
            used_height += node_h
            
        return combined_output
    
    def reset(self):
        self.nodes = []
        return self
