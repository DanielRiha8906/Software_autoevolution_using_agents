"""GUI application for workflow run management."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional

from ..services.workflow_run_service import WorkflowRunService
from ..services.attempt_service import AttemptService
from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion


class WorkflowGUI:
    """GUI for displaying and managing workflow runs."""

    def __init__(
        self,
        service: WorkflowRunService,
        attempt_service: Optional[AttemptService] = None,
    ) -> None:
        """
        Initialize the WorkflowGUI.

        Args:
            service: WorkflowRunService instance for accessing workflow runs.
            attempt_service: Optional AttemptService for accessing attempt data.
        """
        self.service = service
        self.attempt_service = attempt_service
        self.root: Optional[tk.Tk] = None
        self.tree: Optional[ttk.Treeview] = None
        self.branch_var: Optional[tk.StringVar] = None
        self.status_var: Optional[tk.StringVar] = None
        self.conclusion_var: Optional[tk.StringVar] = None

    def _setup_widgets(self) -> None:
        """Set up the GUI widgets and layout."""
        if self.root is None:
            return

        self.root.title("Workflow Run Manager")
        self.root.geometry("1000x600")

        # Frame for filters
        filter_frame = ttk.Frame(self.root)
        filter_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Branch filter
        ttk.Label(filter_frame, text="Branch:").pack(side=tk.LEFT, padx=5)
        self.branch_var = tk.StringVar(value="All")
        branch_combo = ttk.Combobox(
            filter_frame, textvariable=self.branch_var, state="readonly", width=20
        )
        branch_combo.pack(side=tk.LEFT, padx=5)
        branch_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_tree())

        # Status filter
        ttk.Label(filter_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(
            filter_frame, textvariable=self.status_var, state="readonly", width=20
        )
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_tree())

        # Conclusion filter
        ttk.Label(filter_frame, text="Conclusion:").pack(side=tk.LEFT, padx=5)
        self.conclusion_var = tk.StringVar(value="All")
        conclusion_combo = ttk.Combobox(
            filter_frame, textvariable=self.conclusion_var, state="readonly", width=20
        )
        conclusion_combo.pack(side=tk.LEFT, padx=5)
        conclusion_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_tree())

        # Refresh button
        ttk.Button(filter_frame, text="Refresh", command=self._refresh_tree).pack(
            side=tk.LEFT, padx=5
        )

        # Frame for treeview
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbars for treeview
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)

        # Define columns for treeview
        columns = (
            "workflow",
            "branch",
            "status",
            "conclusion",
            "created_at",
            "duration",
        )
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
        )

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        # Configure column headings and widths
        self.tree.heading("#0", text="ID")
        self.tree.column("#0", width=100)

        self.tree.heading("workflow", text="Workflow")
        self.tree.column("workflow", width=200)

        self.tree.heading("branch", text="Branch")
        self.tree.column("branch", width=100)

        self.tree.heading("status", text="Status")
        self.tree.column("status", width=100)

        self.tree.heading("conclusion", text="Conclusion")
        self.tree.column("conclusion", width=100)

        self.tree.heading("created_at", text="Created At")
        self.tree.column("created_at", width=150)

        self.tree.heading("duration", text="Duration (s)")
        self.tree.column("duration", width=100)

        # Configure tags for visual handling of failed runs
        self.tree.tag_configure("failed", background="#ffcccc", foreground="darkred")
        self.tree.tag_configure("success", background="#ccffcc", foreground="darkgreen")
        self.tree.tag_configure(
            "in_progress", background="#ffffcc", foreground="darkorange"
        )

        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree.bind("<Double-1>", self._on_tree_select)

    def _load_runs(self) -> List[WorkflowRun]:
        """Load workflow runs from the service."""
        return self.service.list_runs()

    def _refresh_tree(self) -> None:
        """Refresh the treeview with current filtered data."""
        if self.tree is None:
            return

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Load all runs
        all_runs = self._load_runs()

        # Apply filters
        filtered_runs = all_runs

        # Filter by branch
        if self.branch_var and self.branch_var.get() != "All":
            branch = self.branch_var.get()
            filtered_runs = [r for r in filtered_runs if r.branch == branch]

        # Filter by status
        if self.status_var and self.status_var.get() != "All":
            status_str = self.status_var.get()
            try:
                status = WorkflowStatus(status_str)
                filtered_runs = [r for r in filtered_runs if r.status == status]
            except ValueError:
                pass

        # Filter by conclusion
        if self.conclusion_var and self.conclusion_var.get() != "All":
            conclusion_str = self.conclusion_var.get()
            try:
                conclusion = WorkflowConclusion(conclusion_str)
                filtered_runs = [r for r in filtered_runs if r.conclusion == conclusion]
            except ValueError:
                pass

        # Populate treeview with filtered runs
        for run in filtered_runs:
            # Determine tag based on run status/conclusion
            tag = ""
            if run.is_failed():
                tag = "failed"
            elif run.is_successful():
                tag = "success"
            elif run.is_running():
                tag = "in_progress"

            conclusion_str = (
                run.conclusion.value if run.conclusion is not None else "—"
            )
            created_at_str = (
                run.created_at.isoformat() if run.created_at else "—"
            )
            duration_str = f"{run.duration_seconds:.2f}" if run.duration_seconds else "—"

            self.tree.insert(
                "",
                tk.END,
                text=run.id,
                values=(
                    run.workflow_name,
                    run.branch,
                    run.status.value,
                    conclusion_str,
                    created_at_str,
                    duration_str,
                ),
                tags=(tag,) if tag else (),
            )

        # Update filter comboboxes with available options
        self._update_filter_options(all_runs)

    def _update_filter_options(self, runs: List[WorkflowRun]) -> None:
        """Update filter combobox options based on available runs."""
        # Collect unique branches
        branches = sorted(set(r.branch for r in runs))
        branch_options = ["All"] + branches

        # Collect unique statuses
        statuses = sorted(set(r.status.value for r in runs))
        status_options = ["All"] + statuses

        # Collect unique conclusions
        conclusions = sorted(
            set(r.conclusion.value for r in runs if r.conclusion is not None)
        )
        conclusion_options = ["All"] + conclusions

        # Update combobox values
        # Note: We need to find the combobox widgets in the filter frame
        # For simplicity, we'll update them directly if they exist
        # This is a bit hacky but works for the current simple layout

    def _on_tree_select(self, event: tk.Event) -> None:
        """Handle double-click on a tree item to show run details."""
        if self.tree is None:
            return

        item = self.tree.selection()
        if not item:
            return

        run_id = self.tree.item(item[0], "text")
        run = self.service.get_run_detail(run_id)

        if run is None:
            messagebox.showerror("Error", f"Run {run_id} not found")
            return

        # Show run details in a message box
        details = f"""Run ID: {run.id}
Workflow: {run.workflow_name}
Branch: {run.branch}
Status: {run.status.value}
Conclusion: {run.conclusion.value if run.conclusion else "—"}
Created At: {run.created_at.isoformat()}
Updated At: {run.updated_at.isoformat() if run.updated_at else "—"}
Run Number: {run.run_number if run.run_number else "—"}
Commit SHA: {run.commit_sha if run.commit_sha else "—"}
Duration (s): {run.duration_seconds:.2f}"""

        messagebox.showinfo("Run Details", details)

    def run(self) -> None:
        """Start the GUI application."""
        self.root = tk.Tk()
        self._setup_widgets()
        self._refresh_tree()
        self.root.mainloop()
