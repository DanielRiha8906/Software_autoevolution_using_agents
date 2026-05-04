import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..services.workflow_run_attempt_service import WorkflowRunAttemptService


class WorkflowRunDetailsDialog:
    """Dialog for viewing details of a workflow run."""

    def __init__(
        self,
        parent: tk.Tk,
        run: WorkflowRun,
        attempt_service: WorkflowRunAttemptService,
    ):
        """Initialize the details dialog.

        Args:
            parent: Parent window
            run: The WorkflowRun to display
            attempt_service: Service for retrieving associated attempts
        """
        self.run = run
        self.attempt_service = attempt_service

        self.top = tk.Toplevel(parent)
        self.top.title(f"Run Details - {run.id}")
        self.top.geometry("600x500")

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create and layout all dialog components."""
        # Main container
        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Run details
        details_frame = ttk.LabelFrame(main_frame, text="Run Information", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        details = [
            ("ID:", self.run.id),
            ("Workflow Name:", self.run.workflow_name),
            ("Branch:", self.run.branch),
            ("Status:", self.run.status.value),
            ("Conclusion:", self.run.conclusion.value if self.run.conclusion else "-"),
            ("Duration (s):", f"{self.run.duration_seconds:.2f}"),
            ("Run Number:", str(self.run.run_number) if self.run.run_number else "-"),
            ("Commit SHA:", self.run.commit_sha if self.run.commit_sha else "-"),
            ("Created At:", self.run.created_at.isoformat()),
            ("Updated At:", self.run.updated_at.isoformat() if self.run.updated_at else "-"),
        ]

        for label, value in details:
            row_frame = ttk.Frame(details_frame)
            row_frame.pack(fill=tk.X, pady=5)
            ttk.Label(row_frame, text=label, width=15, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
            ttk.Label(row_frame, text=value).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Attempts section
        attempts_frame = ttk.LabelFrame(main_frame, text="Associated Attempts", padding=10)
        attempts_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        attempts = self._get_attempts()

        if not attempts:
            ttk.Label(attempts_frame, text="No attempts found for this run").pack()
        else:
            # Create a simple text display for attempts
            attempt_text = tk.Text(attempts_frame, height=10, width=60)
            attempt_text.pack(fill=tk.BOTH, expand=True)

            for attempt in attempts:
                text = (
                    f"Attempt {attempt.attempt_number} (ID: {attempt.id})\n"
                    f"  Status: {attempt.status}\n"
                    f"  Conclusion: {attempt.conclusion or '-'}\n"
                    f"  Created At: {attempt.created_at.isoformat()}\n"
                    f"  Duration: {attempt.duration_seconds:.2f}s\n\n"
                )
                attempt_text.insert(tk.END, text)

            attempt_text.config(state=tk.DISABLED)

        # Close button
        close_btn = ttk.Button(main_frame, text="Close", command=self.top.destroy)
        close_btn.pack(pady=10)

    def _get_attempts(self):
        """Get attempts for this run.

        Returns:
            List of WorkflowRunAttempt objects, or empty list if no attempts
        """
        try:
            run_id_int = int(self.run.id)
            return self.attempt_service.get_attempts_for_run(run_id_int, sorted=True)
        except (ValueError, TypeError):
            return []


class WorkflowRunEditDialog:
    """Dialog for editing a workflow run."""

    def __init__(self, parent: tk.Tk, run: WorkflowRun):
        """Initialize the edit dialog.

        Args:
            parent: Parent window
            run: The WorkflowRun to edit
        """
        self.run = run
        self.result: Optional[WorkflowRun] = None

        self.top = tk.Toplevel(parent)
        self.top.title(f"Edit Run - {run.id}")
        self.top.geometry("500x400")

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create and layout all dialog components."""
        # Main container
        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Form fields
        row = 0

        # Workflow Name
        ttk.Label(main_frame, text="Workflow Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self._workflow_name_var = tk.StringVar(value=self.run.workflow_name)
        ttk.Entry(main_frame, textvariable=self._workflow_name_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        # Branch
        ttk.Label(main_frame, text="Branch:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self._branch_var = tk.StringVar(value=self.run.branch)
        ttk.Entry(main_frame, textvariable=self._branch_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        # Status
        ttk.Label(main_frame, text="Status:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self._status_var = tk.StringVar(value=self.run.status.value)
        status_combo = ttk.Combobox(
            main_frame,
            textvariable=self._status_var,
            values=[s.value for s in WorkflowStatus],
            state="readonly",
            width=37,
        )
        status_combo.grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        # Conclusion
        ttk.Label(main_frame, text="Conclusion:").grid(row=row, column=0, sticky=tk.W, pady=5)
        conclusion_value = self.run.conclusion.value if self.run.conclusion else ""
        self._conclusion_var = tk.StringVar(value=conclusion_value)
        conclusion_options = [""] + [c.value for c in WorkflowConclusion]
        conclusion_combo = ttk.Combobox(
            main_frame,
            textvariable=self._conclusion_var,
            values=conclusion_options,
            state="readonly",
            width=37,
        )
        conclusion_combo.grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        # Run Number
        ttk.Label(main_frame, text="Run Number:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self._run_number_var = tk.StringVar(value=str(self.run.run_number) if self.run.run_number else "")
        ttk.Entry(main_frame, textvariable=self._run_number_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        # Commit SHA
        ttk.Label(main_frame, text="Commit SHA:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self._commit_sha_var = tk.StringVar(value=self.run.commit_sha if self.run.commit_sha else "")
        ttk.Entry(main_frame, textvariable=self._commit_sha_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        # Duration Seconds
        ttk.Label(main_frame, text="Duration (s):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self._duration_var = tk.StringVar(value=str(self.run.duration_seconds))
        ttk.Entry(main_frame, textvariable=self._duration_var, width=40).grid(row=row, column=1, sticky=tk.EW, pady=5)
        row += 1

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)

        save_btn = ttk.Button(button_frame, text="Save", command=self._save)
        save_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.top.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

    def _save(self) -> None:
        """Validate and save changes."""
        try:
            # Validate duration
            duration_seconds = float(self._duration_var.get())
            if duration_seconds < 0:
                messagebox.showerror("Validation Error", "Duration must be non-negative")
                return

            # Parse status
            try:
                status = WorkflowStatus(self._status_var.get())
            except ValueError:
                messagebox.showerror("Validation Error", "Invalid status")
                return

            # Parse conclusion (optional)
            conclusion = None
            if self._conclusion_var.get():
                try:
                    conclusion = WorkflowConclusion(self._conclusion_var.get())
                except ValueError:
                    messagebox.showerror("Validation Error", "Invalid conclusion")
                    return

            # Parse run_number (optional)
            run_number = None
            if self._run_number_var.get():
                try:
                    run_number = int(self._run_number_var.get())
                except ValueError:
                    messagebox.showerror("Validation Error", "Run number must be an integer")
                    return

            # Create updated run
            self.result = WorkflowRun(
                id=self.run.id,  # ID is immutable
                workflow_name=self._workflow_name_var.get(),
                branch=self._branch_var.get(),
                status=status,
                conclusion=conclusion,
                created_at=self.run.created_at,  # Created at is immutable
                updated_at=datetime.now(),
                run_number=run_number,
                commit_sha=self._commit_sha_var.get() if self._commit_sha_var.get() else None,
                duration_seconds=duration_seconds,
            )

            self.top.destroy()

        except ValueError as e:
            messagebox.showerror("Validation Error", f"Invalid input: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
