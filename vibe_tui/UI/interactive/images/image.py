from ....base.basic import get_image_box
from ....node.basenode import Node

class UIImage(Node):
    def __init__(self, weight, image_path):
        super().__init__(weight=weight, focusable=False)
        self.img_path = image_path
        
        
    def display(self, width, height):
        return get_image_box(self.img_path, w=width, h=height)