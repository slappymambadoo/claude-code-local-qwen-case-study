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
