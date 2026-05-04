"""UI configuration, operation groupings, and color scheme constants."""

# Window configuration
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600
MIN_WIDTH = 800
MIN_HEIGHT = 600
WINDOW_TITLE = "Calculator GUI"

# Font configuration
FONT_FAMILY = "Arial"
BUTTON_FONT_SIZE = 12
DISPLAY_FONT_SIZE = 14

# Color scheme
COLOR_BG = "#f0f0f0"
COLOR_FG = "#000000"
COLOR_DISPLAY_BG = "#ffffff"
COLOR_BUTTON_BG = "#e0e0e0"
COLOR_BUTTON_FG = "#000000"
COLOR_SUCCESS_BG = "#e8f5e9"
COLOR_ERROR_BG = "#ffebee"
COLOR_ERROR_FG = "#c62828"

# Operation groupings
STANDARD_OPERATIONS = [
    "add",
    "subtract",
    "multiply",
    "divide",
    "square",
    "sqrt",
    "modulo",
    "power",
]

SCIENTIFIC_OPERATIONS = [
    "sin",
    "cos",
    "tan",
    "log",
    "ln",
    "exp",
]

ALL_OPERATIONS = STANDARD_OPERATIONS + SCIENTIFIC_OPERATIONS

# Operation display names
OPERATION_DISPLAY = {
    "add": "Add",
    "subtract": "Subtract",
    "multiply": "Multiply",
    "divide": "Divide",
    "square": "Square",
    "sqrt": "Sqrt",
    "power": "Power",
    "modulo": "Modulo",
    "sin": "Sin",
    "cos": "Cos",
    "tan": "Tan",
    "log": "Log",
    "ln": "Ln",
    "exp": "Exp",
}

# Padding and spacing
PADDING_STANDARD = 10
PADDING_SMALL = 5

# Button dimensions
BUTTON_WIDTH = 15
BUTTON_HEIGHT = 2
