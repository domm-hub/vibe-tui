from .UI import *
from .layouts.baselayouts import UiContainerHorizontal, UiContainerVertical
from .managers.manager import FocusManager
from .managers.app import App
from .managers.eapp import EApp
from .base import *
from .node import *
from .keyinput import *

__version__ = "0.8.0"
__author__  = "Adam Hany"
__license__ = "MIT license"


from .init import initialize

init_obj = initialize()
config = init_obj["config"]

from .statements import set_const

set_const(config)
