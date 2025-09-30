"""
ABOUTME: Formatting utilities for consistent output display across different data types
ABOUTME: Provides helpers for tables, pull requests, comments, and structured data display
"""

from typing import Any, Dict, List
from rich.table import Table
from rich.console import Console

console = Console()


def format_pull_request(pr_data: Dict[str, Any], detailed: bool = False) -> None:
    """Format pull request data for display."""
    if detailed:
        # Use the detailed formatting from output.py
        from .output import format_pull_request_output
        format_pull_request_output(pr_data)
    else:
        # Simple one-line format
        console.print(f"#{pr_data['id']} {pr_data['title']} ({pr_data['state']})")


def format_comment(comment_data: Dict[str, Any]) -> None:
    """Format comment data for display."""
    from .output import format_comment_output
    format_comment_output(comment_data)


def format_table(data: List[Dict[str, Any]], columns: List[str], title: str = None) -> Table:
    """Create a formatted table from data."""
    table = Table(title=title)
    
    # Add columns
    for column in columns:
        table.add_column(column.title(), style="cyan")
    
    # Add rows
    for row in data:
        values = [str(row.get(col, "")) for col in columns]
        table.add_row(*values)
    
    return table