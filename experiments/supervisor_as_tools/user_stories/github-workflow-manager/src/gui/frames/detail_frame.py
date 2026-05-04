import tkinter as tk
from typing import Optional

from ...models.workflow_run import WorkflowRun


class DetailFrame(tk.Frame):
    """Read-only display of workflow run details."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self._run: Optional[WorkflowRun] = None

        # Title
        title = tk.Label(self, text="Run Details", font=("Arial", 12, "bold"))
        title.pack(anchor="w", padx=10, pady=10)

        # Text widget for display (read-only)
        self._text = tk.Text(
            self, height=15, width=60, state="disabled", wrap="word", relief="sunken", bd=1
        )
        self._text.pack(padx=10, pady=5, fill="both", expand=True)

    def set_run(self, run: Optional[WorkflowRun]) -> None:
        """Set the run to display.

        Args:
            run: The WorkflowRun to display, or None to clear
        """
        self._run = run
        self._render()

    def _render(self) -> None:
        """Render the current run details."""
        self._text.config(state="normal")
        self._text.delete("1.0", "end")

        if self._run is None:
            self._text.insert("end", "(No run selected)")
        else:
            conclusion = self._run.conclusion.value if self._run.conclusion else "—"
            text = (
                f"ID: {self._run.id}\n"
                f"Workflow: {self._run.workflow_name}\n"
                f"Branch: {self._run.branch}\n"
                f"Status: {self._run.status.value}\n"
                f"Conclusion: {conclusion}\n"
                f"Run Number: {self._run.run_number or '—'}\n"
                f"Commit SHA: {self._run.commit_sha or '—'}\n"
                f"Created: {self._run.created_at.isoformat()}\n"
                f"Updated: {self._run.updated_at.isoformat() if self._run.updated_at else '—'}\n"
                f"Duration (s): {self._run.duration_seconds}\n"
                f"Attempts: {len(self._run.attempts)}\n"
            )
            self._text.insert("end", text)

        self._text.config(state="disabled")
