class Node:
    def __init__(self, weight=1, focusable=True):
        self.weight = weight
        self.selected = False
        self.color = "" # Stores an ANSI color code
        self.focusable = focusable
        
    def display(self, width, height):
        # Default: Return a block of empty spaces
        return [" " * width for _ in range(height)]
    
class Tab:
    def __init__(self, title, content_node: Node):
        self.title = title
        self.content: Node = content_node
        self.selected = False