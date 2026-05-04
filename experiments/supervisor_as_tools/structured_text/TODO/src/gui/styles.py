"""GUI styling configuration for the TODO Manager."""

COLORS = {
    "overdue_bg": "#ffcccc",
    "overdue_fg": "#cc0000",
    "normal_bg": "#ffffff",
    "normal_fg": "#000000",
}

FONTS = {
    "title": ("Helvetica", 16, "bold"),
    "normal": ("Helvetica", 10),
    "mono": ("Courier", 10),
}

TREEVIEW_TAGS = {
    "overdue": {
        "background": COLORS["overdue_bg"],
        "foreground": COLORS["overdue_fg"],
    },
    "normal": {
        "background": COLORS["normal_bg"],
        "foreground": COLORS["normal_fg"],
    },
}
