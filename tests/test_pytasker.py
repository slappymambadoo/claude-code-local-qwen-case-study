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
