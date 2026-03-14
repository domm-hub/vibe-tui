class Node:
    def __init__(self, weight=1, focusable=True, **kwargs):
        self.weight = weight
        self.selected = False
        self.color = "" # Stores an ANSI color code
        self.focusable = focusable
        self._subscribers = {}
        
    def display(self, width, height):
        # Default: Return a block of empty spaces
        return [" " * width for _ in range(height)]
    
    def on(self, event: str, func):
        """Registers a callback for a specific event."""
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(func)
        return self # Enable method chaining

    def emit(self, event: str, *args, **kwargs):
        """Triggers all registered callbacks for an event."""
        if event in self._subscribers:
            for func in self._subscribers[event]:
                func(*args, **kwargs)

class Tab:
    def __init__(self, title, content_node: Node):
        self.title = title
        self.content: Node = content_node
        self.selected = False