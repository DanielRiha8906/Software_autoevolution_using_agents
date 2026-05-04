import tkinter as tk
from tkinter import messagebox, ttk

from ..services.todo_service import TodoService


class CommentsDialog(tk.Toplevel):
    """Dialog for managing task comments."""

    def __init__(self, parent: tk.Widget, task_id: str, task_title: str, service: TodoService) -> None:
        """
        Initialize CommentsDialog.

        Args:
            parent: Parent widget
            task_id: ID of the task
            task_title: Title of the task
            service: TodoService instance
        """
        super().__init__(parent)
        self.title(f"Comments - {task_title}")
        self.geometry("500x400")
        self.task_id = task_id
        self.service = service

        self._build_widgets()
        self._populate_comments()
        self.transient(parent)
        self.grab_set()

    def _build_widgets(self) -> None:
        """Build dialog widgets."""
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Comments listbox with scrollbar
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.comments_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=10)
        self.comments_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.comments_listbox.yview)

        # Add comment frame
        add_frame = ttk.LabelFrame(frame, text="Add Comment", padding="5")
        add_frame.pack(fill=tk.X, pady=5)

        self.comment_var = tk.StringVar()
        entry = ttk.Entry(add_frame, textvariable=self.comment_var)
        entry.pack(fill=tk.X, side=tk.LEFT, padx=(0, 5))

        ttk.Button(add_frame, text="Add", command=self.on_add_comment).pack(side=tk.LEFT, padx=2)

        # Action buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="Delete Selected", command=self.on_delete_comment).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(button_frame, text="Close", command=self.destroy).pack(side=tk.LEFT, padx=2)

    def _populate_comments(self) -> None:
        """Populate comments listbox."""
        try:
            self.comments_listbox.delete(0, tk.END)
            comments = self.service.list_task_comments(self.task_id)
            self.comments = comments
            for comment in comments:
                preview = comment.content[:70] + ("..." if len(comment.content) > 70 else "")
                self.comments_listbox.insert(tk.END, preview)
            if not comments:
                self.comments_listbox.insert(tk.END, "(no comments)")
                self.comments = []
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load comments: {e}")

    def on_add_comment(self) -> None:
        """Handle add comment button click."""
        content = self.comment_var.get().strip()
        if not content:
            messagebox.showwarning("Warning", "Comment cannot be empty")
            return

        try:
            self.service.add_comment(self.task_id, content)
            self.comment_var.set("")
            self._populate_comments()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add comment: {e}")

    def on_delete_comment(self) -> None:
        """Handle delete comment button click."""
        selection = self.comments_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a comment to delete")
            return

        idx = selection[0]
        if idx >= len(self.comments):
            messagebox.showwarning("Warning", "Invalid selection")
            return

        try:
            comment = self.comments[idx]
            confirm = messagebox.askyesno(
                "Confirm", "Are you sure you want to delete this comment?"
            )
            if confirm:
                self.service.delete_comment(comment.id)
                self._populate_comments()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete comment: {e}")
