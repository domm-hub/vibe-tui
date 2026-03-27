from .layouts import UiContainerHorizontal, UiContainerVertical
from .node import Node

def islayout(m):
    return isinstance(m, (UiContainerHorizontal, UiContainerVertical))

def isnode(m):
    return isinstance(m, Node)

config = None

def set_const(data):
    global config
    config = data