"""Manager module for pytasker - handles business logic and state."""
from typing import List, Dict, Optional
import os
import uuid
from .storage import TaskStorage, StorageError


class TodoNotFoundError(Exception):
    """Raised when a todo item is not found."""
    pass


class InvalidIdError(Exception):
    """Raised when an invalid ID format is provided."""
    pass


class TodoManager:
    """Manages the state and operations for todo items."""

    def __init__(self, storage: Optional[TaskStorage] = None):
        """Initialize the manager with optional custom storage.

        Args:
            storage: Optional TaskStorage instance. Creates default if not provided.
                   If PYTASKER_FILE env var is set and no storage given, uses that path.
        """
        if storage is not None:
            self._storage = storage
        else:
            filepath = os.environ.get('PYTASKER_FILE', 'todos.json')
            self._storage = TaskStorage(filepath)
        self._todos: List[Dict] = []
        self._load_tasks()

    def _load_tasks(self) -> None:
        """Load tasks from storage into memory."""
        try:
            self._todos = self._storage.load_tasks()
        except StorageError as e:
            print(f"Warning: Could not load tasks: {e}")
            self._todos = []

    def _save_tasks(self) -> None:
        """Save tasks from memory to storage."""
        try:
            self._storage.save_tasks(self._todos)
        except StorageError as e:
            print(f"Error: Could not save tasks: {e}")

    def _validate_id(self, id_str: str) -> bool:
        """Validate that an ID string is a valid integer.

        Args:
            id_str: The ID string to validate.

        Returns:
            True if valid, False otherwise.
        """
        try:
            int(id_str)
            return True
        except ValueError:
            return False

    def add_task(self, task_description: str) -> Dict:
        """Add a new todo item.

        Args:
            task_description: Description of the task to add.

        Returns:
            The created todo dictionary.

        Raises:
            ValueError: If task description is empty or whitespace only.
        """
        if not task_description or not task_description.strip():
            raise ValueError("Task description cannot be empty")

        task = {
            "id": len(self._todos) + 1,
            "description": task_description.strip(),
            "completed": False
        }
        self._todos.append(task)
        self._save_tasks()
        return task

    def list_tasks(self) -> List[Dict]:
        """Get all todo items.

        Returns:
            A copy of the todos list.
        """
        return list(self._todos)

    def complete_task(self, id_str: str) -> Dict:
        """Mark a todo item as completed.

        Args:
            id_str: The ID of the task to complete (as string).

        Returns:
            The updated todo dictionary.

        Raises:
            InvalidIdError: If the ID is not a valid integer.
            TodoNotFoundError: If no todo exists with the given ID.
        """
        if not self._validate_id(id_str):
            raise InvalidIdError(f"Invalid ID format: '{id_str}' must be an integer")

        task_id = int(id_str)
        for task in self._todos:
            if task["id"] == task_id:
                task["completed"] = True
                self._save_tasks()
                return task

        raise TodoNotFoundError(f"No todo found with ID: {task_id}")

    def delete_task(self, id_str: str) -> int:
        """Delete a todo item.

        Args:
            id_str: The ID of the task to delete (as string).

        Returns:
            The number of items deleted (always 1 on success).

        Raises:
            InvalidIdError: If the ID is not a valid integer.
            TodoNotFoundError: If no todo exists with the given ID.
        """
        if not self._validate_id(id_str):
            raise InvalidIdError(f"Invalid ID format: '{id_str}' must be an integer")

        task_id = int(id_str)
        for i, task in enumerate(self._todos):
            if task["id"] == task_id:
                self._todos.pop(i)
                # Re-index remaining tasks
                for idx, t in enumerate(self._todos):
                    t["id"] = idx + 1
                self._save_tasks()
                return 1

        raise TodoNotFoundError(f"No todo found with ID: {task_id}")
