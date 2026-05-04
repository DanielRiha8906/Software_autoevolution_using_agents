import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from ...models.workflow_run import WorkflowRun
from ...models.workflow_conclusion import WorkflowConclusion


class ListFrame(tk.Frame):
    """Scrollable table of workflow runs with failed run highlighting."""

    def __init__(self, parent: tk.Widget, on_run_select: Callable[[WorkflowRun], None]) -> None:
        super().__init__(parent)
        self._on_run_select = on_run_select
        self._runs: list[WorkflowRun] = []

        # Title
        title = tk.Label(self, text="Workflow Runs", font=("Arial", 11, "bold"))
        title.pack(anchor="w", padx=10, pady=10)

        # Create Treeview with scrollbar
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")

        self._tree = ttk.Treeview(
            tree_frame,
            columns=("id", "workflow", "branch", "status", "conclusion", "run_number", "attempts"),
            height=12,
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self._tree.yview)

        # Define column headings and widths
        self._tree.column("#0", width=0, stretch="no")
        self._tree.column("id", anchor="w", width=15, minwidth=15)
        self._tree.column("workflow", anchor="w", width=20, minwidth=20)
        self._tree.column("branch", anchor="w", width=15, minwidth=15)
        self._tree.column("status", anchor="w", width=15, minwidth=15)
        self._tree.column("conclusion", anchor="w", width=15, minwidth=15)
        self._tree.column("run_number", anchor="center", width=12, minwidth=12)
        self._tree.column("attempts", anchor="center", width=10, minwidth=10)

        self._tree.heading("#0", text="")
        self._tree.heading("id", text="ID")
        self._tree.heading("workflow", text="Workflow")
        self._tree.heading("branch", text="Branch")
        self._tree.heading("status", text="Status")
        self._tree.heading("conclusion", text="Conclusion")
        self._tree.heading("run_number", text="Run#")
        self._tree.heading("attempts", text="Atts")

        self._tree.pack(fill="both", expand=True)

        # Bind selection event
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # Configure tag for failed runs (red/pink background)
        self._tree.tag_configure("failed", background="#ffcccc")

    def set_runs(self, runs: list[WorkflowRun]) -> None:
        """Update the list with new runs.

        Args:
            runs: List of WorkflowRun objects to display
        """
        self._runs = runs
        self._render()

    def _render(self) -> None:
        """Render the runs in the treeview."""
        # Clear existing items
        for item in self._tree.get_children():
            self._tree.delete(item)

        # Add runs as rows
        for run in self._runs:
            conclusion = run.conclusion.value if run.conclusion else "—"
            run_number = str(run.run_number) if run.run_number is not None else "—"
            attempt_count = str(len(run.attempts))

            tags = []
            if run.conclusion == WorkflowConclusion.FAILURE:
                tags.append("failed")

            self._tree.insert(
                "",
                "end",
                values=(
                    run.id,
                    run.workflow_name,
                    run.branch,
                    run.status.value,
                    conclusion,
                    run_number,
                    attempt_count,
                ),
                tags=tags,
            )

    def _on_select(self, event: tk.Event) -> None:
        """Handle treeview selection."""
        selection = self._tree.selection()
        if not selection:
            return

        # Get the index of the selected item
        selected_index = self._tree.index(selection[0])
        if 0 <= selected_index < len(self._runs):
            self._on_run_select(self._runs[selected_index])
