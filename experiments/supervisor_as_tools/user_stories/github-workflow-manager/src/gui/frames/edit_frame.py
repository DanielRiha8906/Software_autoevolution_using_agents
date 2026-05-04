import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from ...models.workflow_run import WorkflowRun
from ...models.workflow_status import WorkflowStatus
from ...models.workflow_conclusion import WorkflowConclusion


class EditFrame(tk.Frame):
    """Edit form with validation (overlay frame, not modal)."""

    def __init__(
        self,
        parent: tk.Widget,
        on_save: Callable[[WorkflowRun], None],
        on_cancel: Callable,
    ) -> None:
        super().__init__(parent)
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._run: Optional[WorkflowRun] = None

        # Title
        title = tk.Label(self, text="Edit Run", font=("Arial", 12, "bold"))
        title.pack(anchor="w", padx=10, pady=10)

        # Form frame
        form_frame = tk.Frame(self)
        form_frame.pack(fill="x", padx=10, pady=5)

        # ID (read-only)
        tk.Label(form_frame, text="ID:").grid(row=0, column=0, sticky="w", pady=5)
        self._id_var = tk.StringVar()
        id_entry = tk.Entry(form_frame, textvariable=self._id_var, state="readonly", width=30)
        id_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # Workflow name
        tk.Label(form_frame, text="Workflow:").grid(row=1, column=0, sticky="w", pady=5)
        self._workflow_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self._workflow_var, width=30).grid(
            row=1, column=1, sticky="w", padx=5, pady=5
        )

        # Branch
        tk.Label(form_frame, text="Branch:").grid(row=2, column=0, sticky="w", pady=5)
        self._branch_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self._branch_var, width=30).grid(
            row=2, column=1, sticky="w", padx=5, pady=5
        )

        # Status
        tk.Label(form_frame, text="Status:").grid(row=3, column=0, sticky="w", pady=5)
        self._status_var = tk.StringVar()
        status_options = [s.value for s in WorkflowStatus]
        ttk.Combobox(form_frame, textvariable=self._status_var, values=status_options, state="readonly", width=27).grid(
            row=3, column=1, sticky="w", padx=5, pady=5
        )

        # Conclusion
        tk.Label(form_frame, text="Conclusion:").grid(row=4, column=0, sticky="w", pady=5)
        self._conclusion_var = tk.StringVar()
        conclusion_options = [""] + [c.value for c in WorkflowConclusion]
        ttk.Combobox(
            form_frame, textvariable=self._conclusion_var, values=conclusion_options, state="readonly", width=27
        ).grid(row=4, column=1, sticky="w", padx=5, pady=5)

        # Run number
        tk.Label(form_frame, text="Run Number:").grid(row=5, column=0, sticky="w", pady=5)
        self._run_number_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self._run_number_var, width=30).grid(
            row=5, column=1, sticky="w", padx=5, pady=5
        )

        # Duration (seconds)
        tk.Label(form_frame, text="Duration (s):").grid(row=6, column=0, sticky="w", pady=5)
        self._duration_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self._duration_var, width=30).grid(
            row=6, column=1, sticky="w", padx=5, pady=5
        )

        # Status label for error messages
        self._status_label = tk.Label(form_frame, text="", fg="red", wraplength=300)
        self._status_label.grid(row=7, column=0, columnspan=2, sticky="w", pady=5)

        # Button frame
        button_frame = tk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(button_frame, text="Save", command=self._save).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side="left", padx=5)

    def set_run(self, run: WorkflowRun) -> None:
        """Load a run for editing.

        Args:
            run: The WorkflowRun to edit
        """
        self._run = run
        self._clear_status()

        self._id_var.set(run.id)
        self._workflow_var.set(run.workflow_name)
        self._branch_var.set(run.branch)
        self._status_var.set(run.status.value)
        self._conclusion_var.set(run.conclusion.value if run.conclusion else "")
        self._run_number_var.set(str(run.run_number) if run.run_number is not None else "")
        self._duration_var.set(str(run.duration_seconds))

    def _clear_status(self) -> None:
        """Clear the status/error message."""
        self._status_label.config(text="", fg="red")

    def _set_status(self, message: str, error: bool = True) -> None:
        """Display a status/error message.

        Args:
            message: The message to display
            error: If True, show in red; otherwise green
        """
        color = "red" if error else "green"
        self._status_label.config(text=message, fg=color)

    def validate_inputs(self) -> bool:
        """Validate form inputs.

        Returns:
            True if valid, False otherwise
        """
        self._clear_status()

        # Validate run_number if provided
        run_number_str = self._run_number_var.get().strip()
        if run_number_str:
            try:
                run_number = int(run_number_str)
                if run_number < 0:
                    self._set_status("Run number cannot be negative.")
                    return False
            except ValueError:
                self._set_status("Run number must be a valid integer.")
                return False

        # Validate duration (non-negative number)
        duration_str = self._duration_var.get().strip()
        if duration_str:
            try:
                duration = float(duration_str)
                if duration < 0:
                    self._set_status("Duration cannot be negative.")
                    return False
            except ValueError:
                self._set_status("Duration must be a valid number.")
                return False

        # Validate status (enum)
        status_val = self._status_var.get().strip()
        if not status_val:
            self._set_status("Status is required.")
            return False
        try:
            WorkflowStatus(status_val)
        except ValueError:
            self._set_status(f"Invalid status: {status_val}")
            return False

        # Validate conclusion (enum or empty)
        conclusion_val = self._conclusion_var.get().strip()
        if conclusion_val:
            try:
                WorkflowConclusion(conclusion_val)
            except ValueError:
                self._set_status(f"Invalid conclusion: {conclusion_val}")
                return False

        return True

    def _save(self) -> None:
        """Save the edited run."""
        if not self.validate_inputs():
            return

        if self._run is None:
            self._set_status("No run loaded.")
            return

        # Update run object
        self._run.workflow_name = self._workflow_var.get().strip()
        self._run.branch = self._branch_var.get().strip()
        self._run.status = WorkflowStatus(self._status_var.get())

        conclusion_val = self._conclusion_var.get().strip()
        self._run.conclusion = WorkflowConclusion(conclusion_val) if conclusion_val else None

        run_number_str = self._run_number_var.get().strip()
        self._run.run_number = int(run_number_str) if run_number_str else None

        duration_str = self._duration_var.get().strip()
        self._run.duration_seconds = float(duration_str) if duration_str else 0.0

        # Call save callback
        try:
            self._on_save(self._run)
            self._set_status("Saved successfully.", error=False)
        except ValueError as e:
            self._set_status(f"Error saving: {e}")
