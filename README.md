# Vibe-TUI

A TUI library based in pure python that uses weighting to align your program perfectly.

![Version](https://img.shields.io/badge/version-0.3.0--Beta-orange)
![Creator](https://img.shields.io/badge/creator-Adam%20Hany-blue)

### Why should I use this?
- No `asyncio`: Do what you want and manage as you like and display when you're finished; no rush here!
- Weight based alignment: Remove the hassle of calculating widths and heights to the weight system! (I don't see hackers need to be game devs to make good TUIs)

### What Nodes (or widgets) can I use?
- `UIBox`: A.. box
- `PyCodeText(UIBox)` (In progress): Python text editor.
- `UILabel(UIBox)`: a box without the box part (without edges)
- `UIBar(UIBox)`: Loading bar, requires vibe_loadbar to be installed
- `ColorPicker(UIBox)`: A colour picker
- `UICheckbox(UIBox)`: A checkbox
- `UIInput(UIBox)`: A text input
- `UISelect(UIBox)`: A selection manager.
- `TabManagerH(UIBox)`: A tab manager.
- `UIScrollText(UIBox)`: Scrollable text view.
- `UIModal(Node)`: A Modal

### What layouts can I use?
- `UiContainerHorizontal(Node)`: Horizontal layout.
- `UiContainerVertical(Node)`: Vertical layout

You can also use `FocusManager` to manage Node focus.

### File Structure:
```
.
├── README.md
└── vibe_tui
    ├── UI
    │   ├── __init__.py
    │   ├── base_widgets.py
    │   ├── interactive
    │   │   ├── __init__.py
    │   │   ├── clickable.py
    │   │   └── textinput.py
    │   └── widgets.py
    ├── __init__.py
    ├── base
    │   ├── __init__.py
    │   ├── basic.py
    │   └── colors.py
    ├── layouts
    │   ├── __init__.py
    │   └── baselayouts.py
    ├── managers
    │   ├── __init__.py
    │   └── manager.py
    └── node
        ├── __init__.py
        └── basenode.py
```

### Class structure:
![class](architecture.svg)

Made with **time** and `code` by **Adam Hany**