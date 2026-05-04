"""Tkinter-based GUI for displaying and filtering workflow runs."""

import tkinter as tk
from tkinter import ttk
from typing import Optional


class WorkflowGUI:
    """A GUI for displaying workflow runs with filtering capability.

    This class provides a tkinter-based interface for viewing workflow runs
    from a service instance. It delegates all logic to the service layer
    and does not instantiate services internally.
    """

    def __init__(self, service):
        """Initialize the WorkflowGUI with a service instance.

        Args:
            service: A service instance that provides access to workflow runs.
                     The service must have methods like list_runs() and
                     filter_by_status(), filter_by_conclusion(), etc.
        """
        self.service = service
        self.root = None
        self.main_frame = None
        self.tree = None
        self.filter_frame = None
        self.status_var = None
        self.conclusion_var = None

    def create_window(self, title: str = "Workflow Manager") -> tk.Tk:
        """Create and return the main tkinter window.

        Args:
            title: The title of the window.

        Returns:
            The root tkinter window.
        """
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("1000x600")

        self._create_filter_ui()
        self._create_tree_view()

        return self.root

    def _create_filter_ui(self) -> None:
        """Create the filtering UI elements."""
        self.filter_frame = ttk.Frame(self.root)
        self.filter_frame.pack(fill=tk.X, padx=5, pady=5)

        # Status filter
        ttk.Label(self.filter_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(
            self.filter_frame,
            textvariable=self.status_var,
            values=["All", "queued", "in_progress", "completed"],
            state="readonly",
            width=15,
        )
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_runs())

        # Conclusion filter
        ttk.Label(self.filter_frame, text="Conclusion:").pack(side=tk.LEFT, padx=5)
        self.conclusion_var = tk.StringVar(value="All")
        conclusion_combo = ttk.Combobox(
            self.filter_frame,
            textvariable=self.conclusion_var,
            values=[
                "All",
                "success",
                "failure",
                "cancelled",
                "skipped",
                "timed_out",
                "action_required",
                "neutral",
                "stale",
            ],
            state="readonly",
            width=15,
        )
        conclusion_combo.pack(side=tk.LEFT, padx=5)
        conclusion_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_runs())

        # Refresh button
        ttk.Button(
            self.filter_frame,
            text="Refresh",
            command=self.refresh_runs,
        ).pack(side=tk.LEFT, padx=5)

    def _create_tree_view(self) -> None:
        """Create the treeview for displaying workflow runs."""
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Define columns
        columns = ("ID", "Workflow", "Status", "Conclusion", "Branch", "Created", "Duration")

        # Create treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            height=15,
            show="headings",
        )

        # Configure column headings and widths
        self.tree.heading("ID", text="ID")
        self.tree.column("ID", width=150)

        self.tree.heading("Workflow", text="Workflow")
        self.tree.column("Workflow", width=150)

        self.tree.heading("Status", text="Status")
        self.tree.column("Status", width=100)

        self.tree.heading("Conclusion", text="Conclusion")
        self.tree.column("Conclusion", width=100)

        self.tree.heading("Branch", text="Branch")
        self.tree.column("Branch", width=100)

        self.tree.heading("Created", text="Created")
        self.tree.column("Created", width=150)

        self.tree.heading("Duration", text="Duration (s)")
        self.tree.column("Duration", width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Define tag for failed/error runs
        self.tree.tag_configure("failed", foreground="red")
        self.tree.tag_configure("error", foreground="darkred", background="mistyrose")

    def refresh_runs(self) -> None:
        """Refresh the display by fetching runs from the service with applied filters."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get all runs from service
        runs = self.service.list_runs()

        # Apply filters based on UI selections
        status_filter = self.status_var.get()
        conclusion_filter = self.conclusion_var.get()

        filtered_runs = runs

        # Filter by status if not "All"
        if status_filter != "All":
            filtered_runs = [r for r in filtered_runs if r.status.value == status_filter]

        # Filter by conclusion if not "All"
        if conclusion_filter != "All":
            filtered_runs = [r for r in filtered_runs if r.conclusion and r.conclusion.value == conclusion_filter]

        # Insert rows into treeview
        for run in filtered_runs:
            conclusion_text = run.conclusion.value if run.conclusion else "None"

            # Determine tag based on failure or error status
            tag = ""
            if run.is_failed():
                tag = "failed"
            elif run.conclusion and run.conclusion.value in ["error", "timed_out", "action_required"]:
                tag = "error"

            self.tree.insert(
                "",
                tk.END,
                values=(
                    run.id[:8] if len(run.id) > 8 else run.id,
                    run.workflow_name,
                    run.status.value,
                    conclusion_text,
                    run.branch,
                    run.created_at.strftime("%Y-%m-%d %H:%M:%S") if run.created_at else "N/A",
                    f"{run.duration_seconds:.1f}",
                ),
                tags=(tag,) if tag else (),
            )

    def run(self) -> None:
        """Start the tkinter main loop.

        This method should be called after the window is created to display
        and interact with the GUI.
        """
        if self.root is None:
            self.create_window()

        self.refresh_runs()
        self.root.mainloop()
