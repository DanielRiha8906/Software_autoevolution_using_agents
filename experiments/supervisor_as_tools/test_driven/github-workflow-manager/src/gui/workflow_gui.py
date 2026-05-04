import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..services.workflow_run_service import WorkflowRunService


class WorkflowGUI:
    """Tkinter-based GUI for displaying and filtering workflow runs."""

    def __init__(self, service: WorkflowRunService):
        """Initialize the WorkflowGUI with a service instance.

        Args:
            service: WorkflowRunService instance for delegating business logic.
        """
        self.service = service
        self.root = tk.Tk()
        self.root.title("Workflow Run Manager")
        self.root.geometry("1000x600")

        # Store runs for display
        self._current_runs: List[WorkflowRun] = []
        self._selected_run_id: Optional[str] = None

        self._build_ui()
        self._load_runs()

    def _build_ui(self) -> None:
        """Build the GUI layout with title, filters, treeview, and detail panel."""
        # Title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        title_label = ttk.Label(title_frame, text="Workflow Runs", font=("Arial", 16, "bold"))
        title_label.pack()

        # Filter controls
        filter_frame = ttk.LabelFrame(self.root, text="Filters", padding=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        # Branch filter
        ttk.Label(filter_frame, text="Branch:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.branch_entry = ttk.Entry(filter_frame, width=20)
        self.branch_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # Status filter
        ttk.Label(filter_frame, text="Status:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        status_values = [""] + [s.value for s in WorkflowStatus]
        self.status_var = tk.StringVar(value="")
        self.status_dropdown = ttk.Combobox(
            filter_frame, textvariable=self.status_var, values=status_values, state="readonly", width=15
        )
        self.status_dropdown.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        # Conclusion filter
        ttk.Label(filter_frame, text="Conclusion:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        conclusion_values = [""] + [c.value for c in WorkflowConclusion]
        self.conclusion_var = tk.StringVar(value="")
        self.conclusion_dropdown = ttk.Combobox(
            filter_frame, textvariable=self.conclusion_var, values=conclusion_values, state="readonly", width=15
        )
        self.conclusion_dropdown.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # Filter button
        self.filter_button = ttk.Button(filter_frame, text="Apply Filters", command=self._apply_filters)
        self.filter_button.grid(row=1, column=2, padx=5, pady=5)

        # Reset button
        self.reset_button = ttk.Button(filter_frame, text="Reset", command=self._reset_filters)
        self.reset_button.grid(row=1, column=3, padx=5, pady=5)

        # Main display area (Treeview)
        display_frame = ttk.LabelFrame(self.root, text="Runs", padding=5)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create Treeview with scrollbar
        tree_scroll = ttk.Scrollbar(display_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(
            display_frame,
            columns=("id", "workflow", "branch", "status", "conclusion", "duration"),
            height=12,
            yscrollcommand=tree_scroll.set,
        )
        tree_scroll.config(command=self.tree.yview)

        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("id", anchor=tk.W, width=120)
        self.tree.column("workflow", anchor=tk.W, width=150)
        self.tree.column("branch", anchor=tk.W, width=100)
        self.tree.column("status", anchor=tk.W, width=100)
        self.tree.column("conclusion", anchor=tk.W, width=100)
        self.tree.column("duration", anchor=tk.E, width=80)

        self.tree.heading("#0", text="", anchor=tk.W)
        self.tree.heading("id", text="Run ID", anchor=tk.W)
        self.tree.heading("workflow", text="Workflow", anchor=tk.W)
        self.tree.heading("branch", text="Branch", anchor=tk.W)
        self.tree.heading("status", text="Status", anchor=tk.W)
        self.tree.heading("conclusion", text="Conclusion", anchor=tk.W)
        self.tree.heading("duration", text="Duration (s)", anchor=tk.E)

        # Configure tags for styling
        self.tree.tag_configure("failed", foreground="red", font=("Arial", 10, "bold"))
        self.tree.tag_configure("success", foreground="green")

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_run_selected)

        # Detail panel
        detail_frame = ttk.LabelFrame(self.root, text="Run Details", padding=5)
        detail_frame.pack(fill=tk.X, padx=10, pady=5)

        self.detail_text = tk.Text(detail_frame, height=6, width=100, wrap=tk.WORD, state=tk.DISABLED)
        self.detail_text.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var_bar = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var_bar, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _load_runs(self) -> None:
        """Load all runs from service and populate the treeview."""
        try:
            self._current_runs = self.service.list_runs()
            self._populate_treeview(self._current_runs)
            self.status_var_bar.set(f"Loaded {len(self._current_runs)} runs")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load runs: {e}")
            self.status_var_bar.set("Error loading runs")

    def _populate_treeview(self, runs: List[WorkflowRun]) -> None:
        """Clear treeview and populate with given runs."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add runs
        for run in runs:
            conclusion = run.conclusion.value if run.conclusion else "—"
            tags = ()
            if run.is_failed():
                tags = ("failed",)
            elif run.is_successful():
                tags = ("success",)

            self.tree.insert(
                "",
                tk.END,
                iid=run.id,
                values=(
                    run.id,
                    run.workflow_name,
                    run.branch,
                    run.status.value,
                    conclusion,
                    f"{run.duration_seconds:.1f}",
                ),
                tags=tags,
            )

    def _apply_filters(self) -> None:
        """Apply selected filters using service methods."""
        try:
            # Collect filter criteria
            branch = self.branch_entry.get().strip()
            status_val = self.status_var.get()
            conclusion_val = self.conclusion_var.get()

            # Start with all runs
            filtered_runs = self.service.list_runs()

            # Apply branch filter via service
            if branch:
                filtered_runs = self.service.filter_by_branch(branch)

            # Apply status filter via service on the current filtered set
            if status_val:
                status = WorkflowStatus(status_val)
                # Call service method and intersect with current results
                status_filtered = self.service.filter_by_status(status)
                filtered_runs = [r for r in filtered_runs if r in status_filtered]

            # Apply conclusion filter via service on the current filtered set
            if conclusion_val:
                conclusion = WorkflowConclusion(conclusion_val)
                # Call service method and intersect with current results
                conclusion_filtered = self.service.filter_by_conclusion(conclusion)
                filtered_runs = [r for r in filtered_runs if r in conclusion_filtered]

            self._populate_treeview(filtered_runs)
            self.status_var_bar.set(f"Showing {len(filtered_runs)} runs")
        except Exception as e:
            messagebox.showerror("Filter Error", f"Failed to apply filters: {e}")
            self.status_var_bar.set("Error applying filters")

    def _reset_filters(self) -> None:
        """Reset all filters and reload all runs."""
        self.branch_entry.delete(0, tk.END)
        self.status_var.set("")
        self.conclusion_var.set("")
        self._load_runs()
        self._selected_run_id = None
        self._show_detail("")

    def _on_run_selected(self, event) -> None:
        """Handle run selection in treeview."""
        selected = self.tree.selection()
        if selected:
            self._selected_run_id = selected[0]
            self._show_selected_detail()

    def _show_selected_detail(self) -> None:
        """Display details of the selected run."""
        if self._selected_run_id:
            try:
                run = self.service.get_run_detail(self._selected_run_id)
                if run:
                    detail_text = self._format_run_detail(run)
                    self._show_detail(detail_text)
                else:
                    self._show_detail("Run not found")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load run details: {e}")
                self._show_detail("")

    def _format_run_detail(self, run: WorkflowRun) -> str:
        """Format run details for display."""
        conclusion = run.conclusion.value if run.conclusion else "—"
        updated = run.updated_at.isoformat() if run.updated_at else "—"
        return (
            f"ID: {run.id}\n"
            f"Workflow: {run.workflow_name}\n"
            f"Branch: {run.branch}\n"
            f"Status: {run.status.value}\n"
            f"Conclusion: {conclusion}\n"
            f"Duration: {run.duration_seconds:.1f}s\n"
            f"Created: {run.created_at.isoformat()}\n"
            f"Updated: {updated}\n"
            f"Run Number: {run.run_number or '—'}\n"
            f"Commit SHA: {run.commit_sha or '—'}"
        )

    def _show_detail(self, text: str) -> None:
        """Update the detail panel with given text."""
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(tk.END, text)
        self.detail_text.config(state=tk.DISABLED)

    def run(self) -> None:
        """Start the GUI event loop."""
        self.root.mainloop()
