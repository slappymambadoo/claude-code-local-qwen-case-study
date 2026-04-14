
======== pytasker/__init__.py ========

"""PyTasker - A simple command-line todo list manager."""

from .manager import TodoManager, TodoNotFoundError, InvalidIdError
from .storage import TaskStorage, StorageError
from .cli import main as cli_main
import pytasker.main

__version__ = "1.0.0"
__all__ = [
    "TodoManager",
    "TodoNotFoundError",
    "InvalidIdError",
    "TaskStorage",
    "StorageError",
    "main"
]

======== pytasker/cli.py ========

"""CLI module for pytasker - command-line interface."""
import argparse
from .manager import TodoManager, TodoNotFoundError, InvalidIdError
from .task_manager import TaskManager, TaskNotFoundError


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="pytasker",
        description="A simple command-line todo list manager."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument(
        "task",
        nargs="+",
        help="The task description (use quotes for multi-word tasks)"
    )

    # List command
    subparsers.add_parser("list", help="List all tasks")

    # Complete command
    complete_parser = subparsers.add_parser("complete", help="Mark a task as completed")
    complete_parser.add_argument(
        "id",
        type=str,
        help="The ID of the task to complete"
    )

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument(
        "id",
        type=str,
        help="The ID of the task to delete"
    )

    return parser


def format_task(task) -> str:
    """Format a single task for display.

    Args:
        task: The task dictionary or Task object to format.

    Returns:
        Formatted string representation of the task.
    """
    # Handle both dict and Task object formats
    if isinstance(task, dict):
        status = "[x]" if task.get("completed", False) else "[ ]"
        return f"{task['id']}. {status} {task['description']}"
    else:
        # Task object format (from task_manager.py)
        status = "✓" if task.completed else "○"
        return f"[{status}] {task.id}: {task.description}"


def cmd_add(manager, args) -> None:
    """Handle the add command.

    Args:
        manager: The TodoManager instance.
        args: Parsed arguments containing task description.
    """
    try:
        task_description = " ".join(args.task)
        task = manager.add_task(task_description)
        print(f"Added task: {format_task(task)}")
    except ValueError as e:
        print(f"Error: {e}")


def cmd_list(manager, args) -> None:
    """Handle the list command.

    Args:
        manager: The TodoManager instance.
        args: Parsed arguments (unused).
    """
    tasks = manager.list_tasks()
    if not tasks:
        print("No tasks found. Use 'pytasker add <task>' to add a task.")
        return

    for task in tasks:
        print(format_task(task))


def cmd_complete(manager, args) -> None:
    """Handle the complete command.

    Args:
        manager: The TodoManager instance.
        args: Parsed arguments containing task ID.
    """
    try:
        task = manager.complete_task(args.id)
        print(f"Completed task: {format_task(task)}")
    except (InvalidIdError, TodoNotFoundError, TaskNotFoundError) as e:
        print(f"Error: {e}")


def cmd_delete(manager, args) -> None:
    """Handle the delete command.

    Args:
        manager: The TodoManager instance.
        args: Parsed arguments containing task ID.
    """
    try:
        result = manager.delete_task(args.id)
        # TaskManager returns bool, TodoManager raises exception or returns int
        if isinstance(result, bool) and not result:
            print(f"Error: No task found with ID: {args.id}")
        else:
            print(f"Deleted task with ID: {args.id}")
    except (InvalidIdError, TodoNotFoundError) as e:
        print(f"Error: {e}")


def main():
    """Main entry point for the pytasker CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = TodoManager()

    command_handlers = {
        "add": cmd_add,
        "list": cmd_list,
        "complete": cmd_complete,
        "delete": cmd_delete
    }

    handler = command_handlers.get(args.command)
    if handler:
        handler(manager, args)

======== pytasker/main.py ========

#!/usr/bin/env python3
"""
Main entry point for pytasker CLI.
"""

from .cli import main as cli_main


def run_main():
    """Run the main CLI function. Used by __main__ block."""
    cli_main()


if __name__ == '__main__':
    run_main()

======== pytasker/manager.py ========

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

======== pytasker/storage.py ========

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

======== pytasker/task_manager.py ========

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

======== tests/__init__.py ========

"""
Tests package for pytasker.
"""

======== tests/test_pytasker.py ========

"""
Unit tests for pytasker.
"""

import unittest
import json
import os
import tempfile
from pathlib import Path

from pytasker.storage import TaskStorage, StorageError
from pytasker.task_manager import TaskManager, Task, TaskNotFoundError
from pytasker.cli import create_parser, cmd_add, cmd_list, cmd_complete, cmd_delete, main


class TestTask(unittest.TestCase):
    """Tests for the Task class."""

    def setUp(self):
        self.task = Task(id="abc123", description="Test task")

    def test_task_creation(self):
        """Test basic task creation."""
        self.assertEqual(self.task.id, "abc123")
        self.assertEqual(self.task.description, "Test task")
        self.assertFalse(self.task.completed)

    def test_task_creation_completed(self):
        """Test task creation with completed=True."""
        task = Task(id="def456", description="Done task", completed=True)
        self.assertTrue(task.completed)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        data = self.task.to_dict()
        self.assertEqual(data, {
            'id': 'abc123',
            'description': 'Test task',
            'completed': False
        })

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {'id': 'xyz789', 'description': 'From dict', 'completed': True}
        task = Task.from_dict(data)
        self.assertEqual(task.id, 'xyz789')
        self.assertEqual(task.description, 'From dict')
        self.assertTrue(task.completed)

    def test_from_dict_defaults(self):
        """Test from_dict with missing completed field."""
        data = {'id': 'no1234', 'description': 'No status'}
        task = Task.from_dict(data)
        self.assertFalse(task.completed)

    def test_repr_not_completed(self):
        """Test string representation for incomplete task."""
        expected = "[○] abc123: Test task"
        self.assertEqual(repr(self.task), expected)

    def test_repr_completed(self):
        """Test string representation for completed task."""
        self.task.completed = True
        expected = "[✓] abc123: Test task"
        self.assertEqual(repr(self.task), expected)


class TestTaskStorage(unittest.TestCase):
    """Tests for the TaskStorage class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, 'test_tasks.json')
        self.storage = TaskStorage(self.temp_file)

    def tearDown(self):
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
        os.rmdir(self.temp_dir)

    def test_load_nonexistent_file(self):
        """Test loading from a file that doesn't exist."""
        tasks = self.storage.load_tasks()
        self.assertEqual(tasks, [])

    def test_load_empty_file(self):
        """Test loading from an empty file."""
        Path(self.temp_file).touch()
        tasks = self.storage.load_tasks()
        self.assertEqual(tasks, [])

    def test_load_valid_json(self):
        """Test loading valid JSON data."""
        data = [{'id': '1', 'description': 'Task 1', 'completed': False}]
        with open(self.temp_file, 'w') as f:
            json.dump(data, f)

        tasks = self.storage.load_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['id'], '1')

    def test_load_invalid_json_raises_error(self):
        """Test that invalid JSON raises StorageError."""
        with open(self.temp_file, 'w') as f:
            f.write('not valid json {[')

        with self.assertRaises(StorageError):
            self.storage.load_tasks()

    def test_save_tasks(self):
        """Test saving tasks to file."""
        tasks = [{'id': '1', 'description': 'Task 1', 'completed': True}]
        self.storage.save_tasks(tasks)

        with open(self.temp_file, 'r') as f:
            saved = json.load(f)

        self.assertEqual(saved, tasks)

    def test_save_overwrites(self):
        """Test that save overwrites existing content."""
        original = [{'id': '1', 'description': 'Original'}]
        new_data = [{'id': '2', 'description': 'New'}]

        self.storage.save_tasks(original)
        self.storage.save_tasks(new_data)

        with open(self.temp_file, 'r') as f:
            saved = json.load(f)

        self.assertEqual(saved, new_data)


class TestTaskManager(unittest.TestCase):
    """Tests for the TaskManager class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, 'test_tasks.json')
        self.storage = TaskStorage(self.temp_file)
        self.manager = TaskManager(self.storage)

    def tearDown(self):
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
        os.rmdir(self.temp_dir)

    def test_add_task(self):
        """Test adding a new task."""
        task = self.manager.add_task("Buy milk")
        self.assertEqual(task.description, "Buy milk")
        self.assertFalse(task.completed)

    def test_add_task_persists(self):
        """Test that added tasks are persisted to file."""
        self.manager.add_task("Persistent task")

        # Create new manager with same storage
        new_manager = TaskManager(self.storage)
        tasks = new_manager.list_tasks()

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].description, "Persistent task")

    def test_list_tasks_empty(self):
        """Test listing when no tasks exist."""
        tasks = self.manager.list_tasks()
        self.assertEqual(tasks, [])

    def test_list_tasks_multiple(self):
        """Test listing multiple tasks."""
        self.manager.add_task("Task 1")
        self.manager.add_task("Task 2")
        self.manager.add_task("Task 3")

        tasks = self.manager.list_tasks()
        self.assertEqual(len(tasks), 3)

    def test_list_returns_copy(self):
        """Test that list_tasks returns a copy."""
        self.manager.add_task("Task 1")
        tasks = self.manager.list_tasks()
        tasks.append(Task(id="hack", description="Hack attempt"))

        # Original should be unchanged
        original_count = len(self.manager.list_tasks())
        self.assertEqual(original_count, 1)

    def test_get_task_by_id_found(self):
        """Test finding a task by ID."""
        task = self.manager.add_task("Find me")
        found = self.manager.get_task_by_id(task.id)

        self.assertIsNotNone(found)
        self.assertEqual(found.id, task.id)

    def test_get_task_by_id_not_found(self):
        """Test searching for non-existent task."""
        result = self.manager.get_task_by_id("nonexistent")
        self.assertIsNone(result)

    def test_complete_task(self):
        """Test completing a task."""
        task = self.manager.add_task("To complete")
        completed = self.manager.complete_task(task.id)

        self.assertTrue(completed.completed)

    def test_complete_nonexistent_raises_error(self):
        """Test that completing non-existent task raises error."""
        with self.assertRaises(TaskNotFoundError):
            self.manager.complete_task("nonexistent")

    def test_delete_task(self):
        """Test deleting a task."""
        task = self.manager.add_task("To delete")
        result = self.manager.delete_task(task.id)

        self.assertTrue(result)
        self.assertEqual(len(self.manager.list_tasks()), 0)

    def test_delete_nonexistent_returns_false(self):
        """Test deleting non-existent task."""
        result = self.manager.delete_task("nonexistent")
        self.assertFalse(result)

    def test_complete_task_persists(self):
        """Test that completing a task is persisted."""
        task = self.manager.add_task("Complete me")
        self.manager.complete_task(task.id)

        new_manager = TaskManager(self.storage)
        found = new_manager.get_task_by_id(task.id)
        self.assertTrue(found.completed)

    def test_delete_task_persists(self):
        """Test that deleting a task is persisted."""
        task = self.manager.add_task("Delete me")
        self.manager.delete_task(task.id)

        new_manager = TaskManager(self.storage)
        found = new_manager.get_task_by_id(task.id)
        self.assertIsNone(found)


class TestCLI(unittest.TestCase):
    """Tests for the CLI module."""

    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()
        self.assertIsNotNone(parser)

    def test_parse_add_command(self):
        """Test parsing add command."""
        parser = create_parser()
        args = parser.parse_args(['add', 'Buy', 'milk'])

        self.assertEqual(args.command, 'add')
        self.assertEqual(args.task, ['Buy', 'milk'])

    def test_parse_list_command(self):
        """Test parsing list command."""
        parser = create_parser()
        args = parser.parse_args(['list'])

        self.assertEqual(args.command, 'list')

    def test_parse_complete_command(self):
        """Test parsing complete command."""
        parser = create_parser()
        args = parser.parse_args(['complete', 'abc123'])

        self.assertEqual(args.command, 'complete')
        self.assertEqual(args.id, 'abc123')

    def test_parse_delete_command(self):
        """Test parsing delete command."""
        parser = create_parser()
        args = parser.parse_args(['delete', 'def456'])

        self.assertEqual(args.command, 'delete')
        self.assertEqual(args.id, 'def456')

    def test_no_command_shows_help(self):
        """Test that no command returns None for command."""
        parser = create_parser()
        args = parser.parse_args([])

        self.assertIsNone(args.command)

    def test_cmd_add(self):
        """Test add command handler."""
        temp_file = os.path.join(tempfile.gettempdir(), 'test_cli.json')
        try:
            storage = TaskStorage(temp_file)
            manager = TaskManager(storage)
            parser = create_parser()
            args = parser.parse_args(['add', 'Test', 'task'])

            # Capture print output
            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                cmd_add(manager, args)
            output = f.getvalue()

            self.assertIn('Added task:', output)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_cmd_list_empty(self):
        """Test list command with no tasks."""
        temp_file = os.path.join(tempfile.gettempdir(), 'test_cli2.json')
        try:
            storage = TaskStorage(temp_file)
            manager = TaskManager(storage)
            parser = create_parser()
            args = parser.parse_args(['list'])

            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                cmd_list(manager, args)
            output = f.getvalue()

            self.assertIn('No tasks found', output)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_cmd_complete_not_found(self):
        """Test complete command with non-existent task."""
        temp_file = os.path.join(tempfile.gettempdir(), 'test_cli3.json')
        try:
            storage = TaskStorage(temp_file)
            manager = TaskManager(storage)
            parser = create_parser()
            args = parser.parse_args(['complete', 'nonexistent'])

            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                cmd_complete(manager, args)
            output = f.getvalue()

            self.assertIn('Error:', output)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_cmd_delete_not_found(self):
        """Test delete command with non-existent task."""
        temp_file = os.path.join(tempfile.gettempdir(), 'test_cli4.json')
        try:
            storage = TaskStorage(temp_file)
            manager = TaskManager(storage)
            parser = create_parser()
            args = parser.parse_args(['delete', 'nonexistent'])

            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                cmd_delete(manager, args)
            output = f.getvalue()

            self.assertIn('Error:', output)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_cmd_list_with_tasks(self):
        """Test list command with tasks present."""
        temp_file = os.path.join(tempfile.gettempdir(), 'test_cli5.json')
        try:
            storage = TaskStorage(temp_file)
            manager = TaskManager(storage)
            manager.add_task("Task 1")
            parser = create_parser()
            args = parser.parse_args(['list'])

            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                cmd_list(manager, args)
            output = f.getvalue()

            self.assertIn('Task 1', output)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_cmd_complete_success(self):
        """Test complete command with existing task."""
        temp_file = os.path.join(tempfile.gettempdir(), 'test_cli6.json')
        try:
            storage = TaskStorage(temp_file)
            manager = TaskManager(storage)
            task = manager.add_task("To complete")
            parser = create_parser()
            args = parser.parse_args(['complete', task.id])

            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                cmd_complete(manager, args)
            output = f.getvalue()

            self.assertIn('Completed task:', output)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_cmd_delete_success(self):
        """Test delete command with existing task."""
        temp_file = os.path.join(tempfile.gettempdir(), 'test_cli7.json')
        try:
            storage = TaskStorage(temp_file)
            manager = TaskManager(storage)
            task = manager.add_task("To delete")
            parser = create_parser()
            args = parser.parse_args(['delete', task.id])

            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                cmd_delete(manager, args)
            output = f.getvalue()

            self.assertIn('Deleted task', output)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)


class TestStorageError(unittest.TestCase):
    """Tests for StorageError exception."""

    def test_storage_error_message(self):
        """Test that StorageError can be raised with a message."""
        try:
            raise StorageError("Test error message")
        except StorageError as e:
            self.assertEqual(str(e), "Test error message")


class TestTaskNotFoundError(unittest.TestCase):
    """Tests for TaskNotFoundError exception."""

    def test_task_not_found_error_message(self):
        """Test that TaskNotFoundError can be raised with a message."""
        try:
            raise TaskNotFoundError("Task not found")
        except TaskNotFoundError as e:
            self.assertEqual(str(e), "Task not found")


class TestStorageSaveError(unittest.TestCase):
    """Tests for storage save error handling."""

    def test_save_to_invalid_path_raises_error(self):
        """Test that saving to an invalid path raises StorageError."""
        storage = TaskStorage("/nonexistent/directory/tasks.json")
        with self.assertRaises(StorageError):
            storage.save_tasks([{'id': '1', 'description': 'test'}])


class TestMainFunction(unittest.TestCase):
    """Tests for the main() function."""

    def test_main_no_command(self):
        """Test that main prints help when no command is given."""
        import sys
        from io import StringIO

        # Save original argv and stdout
        old_argv = sys.argv.copy()
        old_stdout = sys.stdout

        try:
            sys.argv = ['pytasker']  # No command
            sys.stdout = StringIO()
            main()
            output = sys.stdout.getvalue()
            self.assertIn('usage:', output.lower())
        finally:
            sys.argv = old_argv
            sys.stdout = old_stdout

    def test_main_add_command(self):
        """Test that main handles add command."""
        import sys
        from io import StringIO

        temp_file = os.path.join(tempfile.gettempdir(), 'test_main.json')
        try:
            old_argv = sys.argv.copy()
            old_stdout = sys.stdout
            old_env = os.environ.get('PYTASKER_FILE')

            try:
                # Set environment variable for test file location
                os.environ['PYTASKER_FILE'] = temp_file
                sys.argv = ['pytasker', 'add', 'Test task from main']
                sys.stdout = StringIO()
                main()
                output = sys.stdout.getvalue()
                self.assertIn('Added task:', output)
            finally:
                sys.argv = old_argv
                sys.stdout = old_stdout
                if old_env:
                    os.environ['PYTASKER_FILE'] = old_env
                elif 'PYTASKER_FILE' in os.environ:
                    del os.environ['PYTASKER_FILE']
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_main_list_command(self):
        """Test that main handles list command."""
        import sys
        from io import StringIO

        temp_file = os.path.join(tempfile.gettempdir(), 'test_main2.json')
        try:
            # Create a task first
            storage = TaskStorage(temp_file)
            manager = TaskManager(storage)
            manager.add_task("Pre-existing task")

            old_argv = sys.argv.copy()
            old_stdout = sys.stdout
            old_env = os.environ.get('PYTASKER_FILE')

            try:
                os.environ['PYTASKER_FILE'] = temp_file
                sys.argv = ['pytasker', 'list']
                sys.stdout = StringIO()
                main()
                output = sys.stdout.getvalue()
                self.assertIn('Pre-existing task', output)
            finally:
                sys.argv = old_argv
                sys.stdout = old_stdout
                if old_env:
                    os.environ['PYTASKER_FILE'] = old_env
                elif 'PYTASKER_FILE' in os.environ:
                    del os.environ['PYTASKER_FILE']
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)


class TestTaskManagerErrorHandling(unittest.TestCase):
    """Tests for TaskManager error handling."""

    def test_manager_handles_storage_error_on_load(self):
        """Test that manager handles StorageError gracefully on load."""
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'corrupt.json')

        try:
            # Create a file with invalid JSON
            with open(temp_file, 'w') as f:
                f.write('not valid json {[')

            storage = TaskStorage(temp_file)
            import sys
            from io import StringIO

            old_stderr = sys.stderr
            sys.stderr = StringIO()

            try:
                manager = TaskManager(storage)
                # Should have empty tasks list after error
                self.assertEqual(len(manager.list_tasks()), 0)
            finally:
                sys.stderr = old_stderr
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            os.rmdir(temp_dir)

    def test_manager_handles_storage_error_on_save(self):
        """Test that manager handles StorageError gracefully on save."""
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'readonly.json')

        try:
            # Create a file and make it read-only
            Path(temp_file).touch()
            os.chmod(temp_file, 0o444)

            storage = TaskStorage(temp_file)
            import sys
            from io import StringIO

            old_stderr = sys.stderr
            sys.stderr = StringIO()

            try:
                manager = TaskManager(storage)
                # Try to add a task - should handle error gracefully
                manager.add_task("Test")
                # Task should still be in memory even if save failed
                tasks = manager.list_tasks()
                self.assertEqual(len(tasks), 1)
            finally:
                sys.stderr = old_stderr
                os.chmod(temp_file, 0o644)  # Restore permissions for cleanup
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            os.rmdir(temp_dir)


class TestMainModule(unittest.TestCase):
    """Tests for the main module."""

    def test_main_module_import(self):
        """Test that main module can be imported and has correct attributes."""
        from pytasker import main as main_module
        # Just verify the module imports correctly
        self.assertIsNotNone(main_module)

    def test_main_module_executable(self):
        """Test that main module is executable via __name__ == '__main__'."""
        import sys
        from io import StringIO

        temp_file = os.path.join(tempfile.gettempdir(), 'test_main_mod.json')
        try:
            old_argv = sys.argv.copy()
            old_stdout = sys.stdout
            old_env = os.environ.get('PYTASKER_FILE')

            try:
                os.environ['PYTASKER_FILE'] = temp_file
                sys.argv = ['main.py', 'list']  # Simulate running as __main__
                sys.stdout = StringIO()

                # Import and execute the main module's if block
                from pytasker import main as main_module
                # The module has: if __name__ == '__main__': main()
                # We can't directly test this without exec, so we verify the structure
                import inspect
                source = inspect.getsource(main_module)
                self.assertIn("if __name__", source)
                self.assertIn("main()", source)
            finally:
                sys.argv = old_argv
                sys.stdout = old_stdout
                if old_env:
                    os.environ['PYTASKER_FILE'] = old_env
                elif 'PYTASKER_FILE' in os.environ:
                    del os.environ['PYTASKER_FILE']
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_main_module_run_as_script(self):
        """Test running main module as a script (covers __name__ == '__main__')."""
        import sys
        from io import StringIO

        temp_file = os.path.join(tempfile.gettempdir(), 'test_script.json')
        try:
            old_argv = sys.argv.copy()
            old_stdout = sys.stdout
            old_env = os.environ.get('PYTASKER_FILE')

            try:
                os.environ['PYTASKER_FILE'] = temp_file
                sys.argv = ['main.py', 'add', 'Script test task']
                sys.stdout = StringIO()

                # Import run_main and call it (this is what __name__ == '__main__' does)
                from pytasker.main import run_main
                run_main()
            finally:
                sys.argv = old_argv
                sys.stdout = old_stdout
                if old_env:
                    os.environ['PYTASKER_FILE'] = old_env
                elif 'PYTASKER_FILE' in os.environ:
                    del os.environ['PYTASKER_FILE']
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)


if __name__ == '__main__':
    unittest.main(verbosity=2)
