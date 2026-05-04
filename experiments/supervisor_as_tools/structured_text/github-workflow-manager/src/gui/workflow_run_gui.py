import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..services.workflow_run_service import WorkflowRunService
from ..services.attempt_service import AttemptService
from ..services.statistics_service import StatisticsService
from .filters import FilterState


class WorkflowRunGUI:
    """GUI viewer for workflow runs.

    Displays workflow runs in a table with filtering, detail view, and attempt tracking.
    """

    def __init__(
        self,
        service: WorkflowRunService,
        attempt_service: AttemptService,
        statistics_service: StatisticsService,
    ) -> None:
        """Initialize WorkflowRunGUI.

        Args:
            service: WorkflowRunService instance.
            attempt_service: AttemptService instance.
            statistics_service: StatisticsService instance.
        """
        self.service = service
        self.attempt_service = attempt_service
        self.statistics_service = statistics_service

        self.root = tk.Tk()
        self.root.title("Workflow Run Viewer")
        self.root.geometry("1400x700")

        self.filter_state = FilterState()
        self.all_runs: List[WorkflowRun] = []

        self._setup_ui()
        self._populate_table()

    def run(self) -> None:
        """Launch the GUI."""
        self.root.mainloop()

    def _setup_ui(self) -> None:
        """Set up the user interface layout."""
        # Top frame: Filter panel
        filter_frame = ttk.LabelFrame(self.root, text="Filters", padding=10)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        # Status filter
        ttk.Label(filter_frame, text="Status:").grid(row=0, column=0, padx=5)
        status_options = [""] + [s.value for s in WorkflowStatus]
        self.status_var = tk.StringVar(value="")
        status_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.status_var,
            values=status_options,
            state="readonly",
            width=20,
        )
        status_combo.grid(row=0, column=1, padx=5)

        # Conclusion filter
        ttk.Label(filter_frame, text="Conclusion:").grid(row=0, column=2, padx=5)
        conclusion_options = [""] + [c.value for c in WorkflowConclusion]
        self.conclusion_var = tk.StringVar(value="")
        conclusion_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.conclusion_var,
            values=conclusion_options,
            state="readonly",
            width=20,
        )
        conclusion_combo.grid(row=0, column=3, padx=5)

        # Apply and Reset buttons
        apply_btn = ttk.Button(filter_frame, text="Apply", command=self._apply_filters)
        apply_btn.grid(row=0, column=4, padx=5)

        reset_btn = ttk.Button(filter_frame, text="Reset", command=self._reset_filters)
        reset_btn.grid(row=0, column=5, padx=5)

        # Middle frame: Table and detail panel
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel: Treeview
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(table_frame, text="Workflow Runs").pack(anchor=tk.W)

        # Create treeview with columns
        columns = (
            "ID",
            "Workflow Name",
            "Status",
            "Conclusion",
            "Duration (sec)",
            "Attempt Count",
            "Updated At",
        )
        self.treeview = ttk.Treeview(
            table_frame,
            columns=columns,
            height=20,
            show="headings",
        )

        # Define column headings and widths
        self.treeview.column("#0", width=0, stretch=tk.NO)
        self.treeview.column("ID", anchor=tk.W, width=120)
        self.treeview.column("Workflow Name", anchor=tk.W, width=150)
        self.treeview.column("Status", anchor=tk.CENTER, width=100)
        self.treeview.column("Conclusion", anchor=tk.CENTER, width=100)
        self.treeview.column("Duration (sec)", anchor=tk.CENTER, width=100)
        self.treeview.column("Attempt Count", anchor=tk.CENTER, width=100)
        self.treeview.column("Updated At", anchor=tk.W, width=200)

        for col in columns:
            self.treeview.heading(col, text=col)

        self.treeview.pack(fill=tk.BOTH, expand=True)
        self.treeview.bind("<<TreeviewSelect>>", self._on_row_selected)

        # Right panel: Detail view
        detail_frame = ttk.LabelFrame(main_frame, text="Details", padding=10)
        detail_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))

        self.detail_frame = detail_frame

        # Detail labels
        self.detail_labels: dict = {}
        fields = [
            ("ID", "id"),
            ("Workflow", "workflow"),
            ("Branch", "branch"),
            ("Status", "status"),
            ("Conclusion", "conclusion"),
            ("Created At", "created_at"),
            ("Updated At", "updated_at"),
            ("Duration", "duration"),
        ]

        for label_text, key in fields:
            label = ttk.Label(detail_frame, text=f"{label_text}:")
            label.pack(anchor=tk.W, pady=2)
            value_label = ttk.Label(detail_frame, text="—", wraplength=250)
            value_label.pack(anchor=tk.W, pady=2)
            self.detail_labels[key] = value_label

        # Attempts sub-section
        ttk.Label(detail_frame, text="Attempts:", font=("TkDefaultFont", 10, "bold")).pack(
            anchor=tk.W, pady=(10, 5)
        )

        attempts_frame = ttk.Frame(detail_frame)
        attempts_frame.pack(fill=tk.BOTH, expand=True)

        self.attempts_treeview = ttk.Treeview(
            attempts_frame,
            columns=("Attempt", "Status", "Conclusion", "Duration"),
            height=6,
            show="headings",
        )
        self.attempts_treeview.column("Attempt", anchor=tk.CENTER, width=60)
        self.attempts_treeview.column("Status", anchor=tk.CENTER, width=70)
        self.attempts_treeview.column("Conclusion", anchor=tk.CENTER, width=70)
        self.attempts_treeview.column("Duration", anchor=tk.CENTER, width=70)

        self.attempts_treeview.heading("Attempt", text="Attempt")
        self.attempts_treeview.heading("Status", text="Status")
        self.attempts_treeview.heading("Conclusion", text="Conclusion")
        self.attempts_treeview.heading("Duration", text="Duration")

        self.attempts_treeview.pack(fill=tk.BOTH, expand=True)

    def _populate_table(self) -> None:
        """Populate treeview with all workflow runs."""
        try:
            self.all_runs = self.service.list_runs()
            self._refresh_table()
        except Exception as e:
            self._show_error(f"Failed to load runs: {e}")

    def _refresh_table(self) -> None:
        """Refresh table display with current filtered data."""
        # Clear existing rows
        for item in self.treeview.get_children():
            self.treeview.delete(item)

        # Insert filtered runs
        for run in self.all_runs:
            conclusion_str = run.conclusion.value if run.conclusion else "—"
            updated_at_str = run.updated_at.isoformat() if run.updated_at else "—"

            values = (
                run.id,
                run.workflow_name,
                run.status.value,
                conclusion_str,
                f"{run.duration_seconds:.1f}",
                "0",  # Placeholder for attempt count; will be updated later
                updated_at_str,
            )

            item_id = self.treeview.insert("", tk.END, values=values)

            # Color failed runs light red
            if run.conclusion == WorkflowConclusion.FAILURE:
                self.treeview.item(item_id, tags=("failed",))

        # Configure tag colors
        self.treeview.tag_configure("failed", background="#ffcccc")

    def _apply_filters(self) -> None:
        """Apply status and conclusion filters to runs."""
        try:
            status_str = self.status_var.get().strip()
            conclusion_str = self.conclusion_var.get().strip()

            status = WorkflowStatus(status_str) if status_str else None
            conclusion = WorkflowConclusion(conclusion_str) if conclusion_str else None

            self.filter_state.status = status
            self.filter_state.conclusion = conclusion

            # Apply filters
            filter_params = self.filter_state.to_filter_params()
            filtered = self.service.filter_runs(**filter_params)
            self.all_runs = filtered

            self._refresh_table()
        except ValueError as e:
            self._show_error(f"Filter error: {e}")

    def _reset_filters(self) -> None:
        """Reset all filters and show all runs."""
        self.filter_state.reset()
        self.status_var.set("")
        self.conclusion_var.set("")
        self.all_runs = self.service.list_runs()
        self._refresh_table()

    def _on_row_selected(self, event) -> None:
        """Handle treeview row selection."""
        selection = self.treeview.selection()
        if selection:
            item_id = selection[0]
            self._show_detail(item_id)

    def _show_detail(self, item_id: str) -> None:
        """Show detail view for selected run."""
        values = self.treeview.item(item_id, "values")
        if not values:
            return

        run_id = values[0]
        run = self.service.get_run_detail(run_id)
        if not run:
            self._show_error(f"Run {run_id} not found")
            return

        # Update detail labels
        self.detail_labels["id"].config(text=run.id)
        self.detail_labels["workflow"].config(text=run.workflow_name)
        self.detail_labels["branch"].config(text=run.branch)
        self.detail_labels["status"].config(text=run.status.value)
        conclusion_str = run.conclusion.value if run.conclusion else "—"
        self.detail_labels["conclusion"].config(text=conclusion_str)
        self.detail_labels["created_at"].config(text=run.created_at.isoformat())
        updated_at_str = run.updated_at.isoformat() if run.updated_at else "—"
        self.detail_labels["updated_at"].config(text=updated_at_str)
        self.detail_labels["duration"].config(text=f"{run.duration_seconds:.1f}")

        # Show attempts
        self._show_attempts(run)

    def _show_attempts(self, run: WorkflowRun) -> None:
        """Show attempts for a run in the sub-treeview."""
        # Clear existing attempts
        for item in self.attempts_treeview.get_children():
            self.attempts_treeview.delete(item)

        # Get attempts for this run
        try:
            run_id_int = int(run.id) if isinstance(run.id, str) else run.id
        except (ValueError, TypeError):
            return

        attempts = self.attempt_service.get_attempts_by_run_id(run_id_int)

        for attempt in attempts:
            conclusion_str = attempt.conclusion or "—"
            values = (
                f"{attempt.attempt_number}",
                attempt.status,
                conclusion_str,
                f"{attempt.duration_seconds:.1f}",
            )
            self.attempts_treeview.insert("", tk.END, values=values)

    def _show_error(self, message: str) -> None:
        """Show error messagebox.

        Args:
            message: Error message to display.
        """
        messagebox.showerror("Error", message)
