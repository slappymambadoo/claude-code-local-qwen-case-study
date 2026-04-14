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
