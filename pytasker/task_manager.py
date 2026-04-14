"""
Task manager module for pytasker - handles task operations.
"""

from typing import List, Dict, Optional
import uuid
import os
from .storage import TaskStorage, StorageError


class TaskNotFoundError(Exception):
    """Raised when a task is not found."""
    pass


class Task:
    """Represents a single todo item."""

    def __init__(self, id: str, description: str, completed: bool = False):
        self.id = id
        self.description = description
        self.completed = completed

    def to_dict(self) -> Dict:
        """Convert task to dictionary representation."""
        return {
            'id': self.id,
            'description': self.description,
            'completed': self.completed
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """Create a Task instance from a dictionary."""
        return cls(
            id=data['id'],
            description=data['description'],
            completed=data.get('completed', False)
        )

    def __repr__(self):
        status = "✓" if self.completed else "○"
        return f"[{status}] {self.id}: {self.description}"


class TaskManager:
    """Manages a collection of tasks with CRUD operations."""

    def __init__(self, storage: Optional[TaskStorage] = None):
        """Initialize the task manager.

        Args:
            storage: TaskStorage instance. Creates default if not provided.
                   If PYTASKER_FILE env var is set and no storage given, uses that path.
        """
        if storage is not None:
            self._storage = storage
        else:
            filepath = os.environ.get('PYTASKER_FILE', 'tasks.json')
            self._storage = TaskStorage(filepath)
        self._tasks: List[Task] = []
        self._load_tasks()

    def _load_tasks(self) -> None:
        """Load tasks from storage into memory."""
        try:
            raw_tasks = self._storage.load_tasks()
            self._tasks = [Task.from_dict(t) for t in raw_tasks]
        except StorageError as e:
            print(f"Warning: {e}")
            self._tasks = []

    def _save_tasks(self) -> None:
        """Save current tasks to storage."""
        try:
            raw_tasks = [t.to_dict() for t in self._tasks]
            self._storage.save_tasks(raw_tasks)
        except StorageError as e:
            print(f"Error saving tasks: {e}")

    def add_task(self, description: str) -> Task:
        """Add a new task.

        Args:
            description: The task description.

        Returns:
            The newly created Task object.
        """
        task = Task(id=str(uuid.uuid4())[:8], description=description)
        self._tasks.append(task)
        self._save_tasks()
        return task

    def list_tasks(self) -> List[Task]:
        """Get all tasks.

        Returns:
            List of all Task objects.
        """
        return self._tasks.copy()

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Find a task by its ID.

        Args:
            task_id: The task ID to search for.

        Returns:
            The Task object if found, None otherwise.
        """
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def complete_task(self, task_id: str) -> Task:
        """Mark a task as completed.

        Args:
            task_id: The ID of the task to complete.

        Returns:
            The updated Task object.

        Raises:
            TaskNotFoundError: If no task with the given ID exists.
        """
        task = self.get_task_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task with id '{task_id}' not found")
        task.completed = True
        self._save_tasks()
        return task

    def delete_task(self, task_id: str) -> bool:
        """Delete a task.

        Args:
            task_id: The ID of the task to delete.

        Returns:
            True if a task was deleted, False otherwise.
        """
        for i, task in enumerate(self._tasks):
            if task.id == task_id:
                self._tasks.pop(i)
                self._save_tasks()
                return True
        return False
