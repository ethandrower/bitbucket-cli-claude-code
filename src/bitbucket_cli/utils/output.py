"""
ABOUTME: Output formatting and console utilities for rich terminal display
ABOUTME: Provides consistent styling for success, error, warning, and info messages
"""

import json
import sys
from typing import Any, Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax

console = Console()


def success(message: str) -> None:
    """Display a success message."""
    console.print(f"✓ {message}", style="bold green")


def error(message: str) -> None:
    """Display an error message."""
    console.print(f"✗ {message}", style="bold red")


def warning(message: str) -> None:
    """Display a warning message."""
    console.print(f"⚠ {message}", style="bold yellow")


def info(message: str) -> None:
    """Display an info message."""
    console.print(f"ℹ {message}", style="bold blue")


def handle_output(data: Any, json_output: bool = False, success_message: Optional[str] = None) -> None:
    """
    Handle output formatting based on format preference.
    
    Args:
        data: Data to output
        json_output: Whether to output as JSON
        success_message: Optional success message for non-JSON output
    """
    if json_output:
        console.print(json.dumps(data, indent=2, default=str))
    else:
        if success_message:
            success(success_message)
        
        # Format data based on type
        if isinstance(data, dict):
            format_dict_output(data)
        elif isinstance(data, list):
            format_list_output(data)
        else:
            console.print(str(data))


def format_dict_output(data: Dict[str, Any]) -> None:
    """Format dictionary data for readable output."""
    
    # Special handling for pull request data
    if "id" in data and "title" in data and "state" in data:
        format_pull_request_output(data)
        return
    
    # Special handling for comment data
    if "content" in data and "user" in data:
        format_comment_output(data)
        return
    
    # Generic dictionary formatting
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Key", style="bold cyan", min_width=15)
    table.add_column("Value", style="white")
    
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value, indent=2, default=str)
        table.add_row(str(key), str(value))
    
    console.print(table)


def format_list_output(data: list) -> None:
    """Format list data for readable output."""
    if not data:
        console.print("No items found.", style="yellow")
        return
    
    # Check if it's a list of pull requests
    if all(isinstance(item, dict) and "id" in item and "title" in item for item in data):
        format_pull_request_list(data)
        return
    
    # Check if it's a list of comments
    if all(isinstance(item, dict) and "content" in item and "user" in item for item in data):
        format_comment_list(data)
        return
    
    # Generic list formatting
    for i, item in enumerate(data, 1):
        console.print(f"[bold cyan]{i}.[/bold cyan] {item}")


def format_pull_request_output(pr_data: Dict[str, Any]) -> None:
    """Format single pull request for detailed output."""
    
    # Create title panel
    title_text = Text()
    title_text.append(f"#{pr_data['id']} ", style="bold cyan")
    title_text.append(pr_data['title'], style="bold white")
    
    title_panel = Panel(
        title_text,
        subtitle=f"State: {pr_data['state']}",
        border_style="blue"
    )
    console.print(title_panel)
    
    # Create details table
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="bold cyan", min_width=15)
    table.add_column("Value", style="white")
    
    # Basic info
    table.add_row("Author", pr_data.get("author", {}).get("username", "Unknown"))
    
    # Branch info
    source = pr_data.get("source", {})
    dest = pr_data.get("destination", {})
    if source.get("branch"):
        table.add_row("Source", source["branch"]["name"])
    if dest.get("branch"):
        table.add_row("Destination", dest["branch"]["name"])
    
    # Dates
    if pr_data.get("created_on"):
        table.add_row("Created", pr_data["created_on"][:19].replace("T", " "))
    if pr_data.get("updated_on"):
        table.add_row("Updated", pr_data["updated_on"][:19].replace("T", " "))
    
    # Reviewers
    reviewers = pr_data.get("reviewers", [])
    if reviewers:
        reviewer_names = [r.get("username", "Unknown") for r in reviewers]
        table.add_row("Reviewers", ", ".join(reviewer_names))
    
    # Links
    links = pr_data.get("links", {})
    if links.get("html", {}).get("href"):
        table.add_row("URL", links["html"]["href"])
    
    console.print(table)
    
    # Description
    description = pr_data.get("description", "").strip()
    if description:
        console.print("\n[bold cyan]Description:[/bold cyan]")
        console.print(Panel(description, border_style="dim"))


def format_pull_request_list(pr_list: list) -> None:
    """Format list of pull requests as a table."""
    table = Table(title="Pull Requests")
    table.add_column("ID", style="cyan", width=8)
    table.add_column("Title", style="bold white", min_width=30)
    table.add_column("Author", style="green", width=15)
    table.add_column("State", style="magenta", width=10)
    table.add_column("Created", style="dim", width=12)
    
    for pr in pr_list:
        title = pr.get("title", "")
        if len(title) > 50:
            title = title[:47] + "..."
        
        created = pr.get("created_on", "")[:10] if pr.get("created_on") else ""
        
        table.add_row(
            str(pr.get("id", "")),
            title,
            pr.get("author", {}).get("username", "Unknown"),
            pr.get("state", ""),
            created
        )
    
    console.print(table)


def format_comment_output(comment_data: Dict[str, Any]) -> None:
    """Format single comment for detailed output."""
    user = comment_data.get("user", {})
    content = comment_data.get("content", {})
    
    # Header with user and date
    header = Text()
    header.append(f"Comment #{comment_data.get('id', 'Unknown')}", style="bold cyan")
    header.append(f" by {user.get('username', 'Unknown')}", style="green")
    
    if comment_data.get("created_on"):
        header.append(f" on {comment_data['created_on'][:19].replace('T', ' ')}", style="dim")
    
    console.print(header)
    
    # Inline comment info
    inline = comment_data.get("inline")
    if inline:
        location_info = []
        if inline.get("to", {}).get("path"):
            location_info.append(f"File: {inline['to']['path']}")
        if inline.get("to", {}).get("line"):
            location_info.append(f"Line: {inline['to']['line']}")
        
        if location_info:
            console.print(f"[dim]📍 {' | '.join(location_info)}[/dim]")
    
    # Comment content
    raw_content = content.get("raw", "")
    if raw_content:
        console.print(Panel(raw_content, border_style="dim"))
    
    console.print()


def format_comment_list(comment_list: list) -> None:
    """Format list of comments."""
    for comment in comment_list:
        format_comment_output(comment)


def format_diff_output(diff_text: str) -> None:
    """Format diff text with syntax highlighting."""
    try:
        syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
        console.print(syntax)
    except Exception:
        # Fallback to plain text if syntax highlighting fails
        console.print(diff_text)


def format_activity_output(activity_list: list) -> None:
    """Format activity timeline."""
    if not activity_list:
        console.print("No activity found.", style="yellow")
        return
    
    for activity in activity_list:
        # Determine activity type and format accordingly
        if activity.get("update"):
            update = activity["update"]
            console.print(f"[dim]📝 {update.get('date', '')[:19].replace('T', ' ')}[/dim]")
            console.print(f"[yellow]Update:[/yellow] {update.get('description', 'Updated')}")
        
        elif activity.get("approval"):
            approval = activity["approval"]
            user = approval.get("user", {})
            console.print(f"[dim]✅ {approval.get('date', '')[:19].replace('T', ' ')}[/dim]")
            console.print(f"[green]Approved by:[/green] {user.get('username', 'Unknown')}")
        
        elif activity.get("comment"):
            comment = activity["comment"]
            format_comment_output(comment)
        
        console.print()


def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    console.print(json.dumps(data, indent=2, default=str))


def confirm(message: str, default: bool = False) -> bool:
    """Ask for user confirmation."""
    suffix = " [Y/n]" if default else " [y/N]"
    try:
        response = input(f"{message}{suffix}: ").strip().lower()
        if not response:
            return default
        return response in ("y", "yes", "true", "1")
    except (KeyboardInterrupt, EOFError):
        return False