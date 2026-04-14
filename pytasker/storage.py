"""Storage module for pytasker - handles JSON file persistence."""
import json
import os
from typing import List, Dict


class StorageError(Exception):
    """Custom exception for storage-related errors."""
    pass


class TaskStorage:
    """Manages persistent storage of todo items in a JSON file."""

    def __init__(self, filepath: str = "todos.json"):
        """Initialize storage with the path to the todos file.

        Args:
            filepath: Path to the JSON file for storing todos.
        """
        self.filepath = filepath

    def load_tasks(self) -> List[Dict]:
        """Load tasks from the JSON file.

        Returns:
            A list of task dictionaries. Returns empty list if file doesn't exist.

        Raises:
            StorageError: If file exists but contains invalid JSON or data format.
        """
        if not os.path.exists(self.filepath):
            return []

        try:
            with open(self.filepath, 'r') as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
                if isinstance(data, list):
                    return data
                raise StorageError("Invalid data format: expected a list")
        except json.JSONDecodeError as e:
            raise StorageError(f"Failed to parse JSON file: {e}")

    def save_tasks(self, tasks: List[Dict]) -> None:
        """Save tasks to the JSON file.

        Args:
            tasks: List of task dictionaries to save.

        Raises:
            StorageError: If unable to write to the file.
        """
        try:
            with open(self.filepath, 'w') as f:
                json.dump(tasks, f, indent=2)
        except IOError as e:
            raise StorageError(f"Failed to save tasks: {e}")
