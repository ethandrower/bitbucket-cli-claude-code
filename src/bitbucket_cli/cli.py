#!/usr/bin/env python3
"""
ABOUTME: Main CLI entry point for Bitbucket PR management tool using Click framework
ABOUTME: Handles command parsing, routing, and global options for all PR operations
"""

import json
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .api import BitbucketAPI
from .auth import load_config, save_config, is_authenticated
from .commands import (
    create_pr,
    list_prs,
    show_pr,
    approve_pr,
    unapprove_pr,
    decline_pr,
    merge_pr,
    comment_pr,
    update_pr,
    diff_pr,
    activity_pr,
    review_pr,
)
from .utils.git import get_repository_info
from .utils.output import handle_output, error, success

console = Console()


def validate_auth(f):
    """Decorator to validate that authentication is configured before running commands."""
    import functools
    
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # Skip validation for config command
        if f.__name__ == "config":
            return f(*args, **kwargs)
        
        if not is_authenticated():
            error("Authentication not configured. Run: bb-pr config --help")
            sys.exit(1)
        
        return f(*args, **kwargs)
    
    return wrapper


@click.group()
@click.version_option()
@click.option(
    "--verbose", "-v", 
    is_flag=True, 
    help="Enable verbose logging"
)
@click.option(
    "--no-color", 
    is_flag=True, 
    help="Disable colored output"
)
@click.option(
    "--json", "output_json",
    is_flag=True, 
    help="Output in JSON format"
)
@click.option(
    "--workspace", "-w",
    help="Override default workspace"
)
@click.option(
    "--repo", "-r", 
    help="Override repository name"
)
@click.pass_context
def cli(ctx, verbose, no_color, output_json, workspace, repo):
    """Bitbucket Cloud PR management CLI for Claude Code integration."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["no_color"] = no_color
    ctx.obj["output_json"] = output_json
    ctx.obj["workspace"] = workspace
    ctx.obj["repo"] = repo


@cli.command()
@click.option("--title", "-t", help="PR title")
@click.option("--description", "-d", help="PR description") 
@click.option("--source", "-s", help="Source branch (defaults to current)")
@click.option("--dest", help="Destination branch (defaults to main)")
@click.option("--reviewers", "-r", help="Comma-separated list of reviewers")
@click.option("--close-branch", is_flag=True, help="Close source branch when merged")
@click.option("--template", help="Use PR template file")
@click.option("--web", is_flag=True, help="Open in web browser after creation")
@click.pass_context
@validate_auth
def create(ctx, title, description, source, dest, reviewers, close_branch, template, web):
    """Create a new pull request."""
    try:
        config = load_config()
        api = BitbucketAPI(config)
        
        workspace = ctx.obj["workspace"]
        repo = ctx.obj["repo"]
        
        if not workspace or not repo:
            repo_info = get_repository_info()
            workspace = workspace or repo_info["workspace"]
            repo = repo or repo_info["repo"]
        
        pr = create_pr(
            api, workspace, repo,
            title=title,
            description=description,
            source=source,
            dest=dest,
            reviewers=reviewers,
            close_branch=close_branch,
            template=template,
            web=web
        )
        
        handle_output(pr, ctx.obj["output_json"], "Pull request created successfully")
        
    except Exception as e:
        error(f"Failed to create PR: {e}")
        sys.exit(1)


@cli.command()
@click.option("--state", default="OPEN", help="Filter by state (OPEN, MERGED, DECLINED, SUPERSEDED)")
@click.option("--author", help="Filter by author username")
@click.option("--reviewer", help="Filter by reviewer username")
@click.option("--limit", default=25, help="Number of results per page")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages")
@click.pass_context
@validate_auth
def list(ctx, state, author, reviewer, limit, fetch_all):
    """List pull requests."""
    try:
        config = load_config()
        api = BitbucketAPI(config)
        
        workspace = ctx.obj["workspace"]
        repo = ctx.obj["repo"]
        
        if not workspace or not repo:
            repo_info = get_repository_info()
            workspace = workspace or repo_info["workspace"]
            repo = repo or repo_info["repo"]
        
        prs = list_prs(
            api, workspace, repo,
            state=state,
            author=author,
            reviewer=reviewer,
            limit=limit,
            fetch_all=fetch_all
        )
        
        if ctx.obj["output_json"]:
            click.echo(json.dumps(prs, indent=2))
        else:
            if not prs:
                console.print("No pull requests found.", style="yellow")
                return
                
            table = Table(title="Pull Requests")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="bold")
            table.add_column("Author", style="green")
            table.add_column("State", style="magenta")
            table.add_column("Created", style="dim")
            
            for pr in prs:
                # Handle author field safely - some APIs return different field names
                author_name = (
                    pr.get("author", {}).get("username") or 
                    pr.get("author", {}).get("nickname") or 
                    pr.get("author", {}).get("display_name") or 
                    "Unknown"
                )
                
                table.add_row(
                    str(pr["id"]),
                    pr["title"][:50] + "..." if len(pr["title"]) > 50 else pr["title"],
                    author_name,
                    pr["state"],
                    pr["created_on"][:10]
                )
            
            console.print(table)
        
    except Exception as e:
        error(f"Failed to list PRs: {e}")
        sys.exit(1)


@cli.command()
@click.argument("pr_id", type=int)
@click.option("--web", is_flag=True, help="Open PR in web browser")
@click.option("--comments", is_flag=True, help="Include comments in output")
@click.pass_context
@validate_auth
def show(ctx, pr_id, web, comments):
    """Show detailed information about a pull request."""
    try:
        config = load_config()
        api = BitbucketAPI(config)
        
        workspace = ctx.obj["workspace"]
        repo = ctx.obj["repo"]
        
        if not workspace or not repo:
            repo_info = get_repository_info()
            workspace = workspace or repo_info["workspace"]
            repo = repo or repo_info["repo"]
        
        pr_data = show_pr(api, workspace, repo, pr_id, web=web, include_comments=comments)
        
        handle_output(pr_data, ctx.obj["output_json"], f"PR #{pr_id} details")
        
    except Exception as e:
        error(f"Failed to show PR: {e}")
        sys.exit(1)


@cli.command()
@click.argument("pr_id", type=int)
@click.pass_context
@validate_auth
def approve(ctx, pr_id):
    """Approve a pull request."""
    try:
        config = load_config()
        api = BitbucketAPI(config)
        
        workspace = ctx.obj["workspace"]
        repo = ctx.obj["repo"]
        
        if not workspace or not repo:
            repo_info = get_repository_info()
            workspace = workspace or repo_info["workspace"]
            repo = repo or repo_info["repo"]
        
        result = approve_pr(api, workspace, repo, pr_id)
        success(f"✓ PR #{pr_id} approved successfully")
        
        if ctx.obj["output_json"]:
            click.echo(json.dumps(result, indent=2))
        
    except Exception as e:
        error(f"Failed to approve PR: {e}")
        sys.exit(1)


@cli.command()
@click.argument("pr_id", type=int)
@click.pass_context
@validate_auth
def unapprove(ctx, pr_id):
    """Remove approval from a pull request."""
    try:
        config = load_config()
        api = BitbucketAPI(config)
        
        workspace = ctx.obj["workspace"]
        repo = ctx.obj["repo"]
        
        if not workspace or not repo:
            repo_info = get_repository_info()
            workspace = workspace or repo_info["workspace"]
            repo = repo or repo_info["repo"]
        
        result = unapprove_pr(api, workspace, repo, pr_id)
        success(f"✓ Approval removed from PR #{pr_id}")
        
        if ctx.obj["output_json"]:
            click.echo(json.dumps(result, indent=2))
        
    except Exception as e:
        error(f"Failed to unapprove PR: {e}")
        sys.exit(1)


@cli.command()
@click.argument("pr_id", type=int)
@click.option("--message", "-m", help="Decline message")
@click.pass_context
@validate_auth
def decline(ctx, pr_id, message):
    """Decline a pull request."""
    try:
        config = load_config()
        api = BitbucketAPI(config)
        
        workspace = ctx.obj["workspace"]
        repo = ctx.obj["repo"]
        
        if not workspace or not repo:
            repo_info = get_repository_info()
            workspace = workspace or repo_info["workspace"]
            repo = repo or repo_info["repo"]
        
        result = decline_pr(api, workspace, repo, pr_id, message=message)
        success(f"✓ PR #{pr_id} declined")
        
        if ctx.obj["output_json"]:
            click.echo(json.dumps(result, indent=2))
        
    except Exception as e:
        error(f"Failed to decline PR: {e}")
        sys.exit(1)


@cli.command()
@click.argument("pr_id", type=int)
@click.option("--message", "-m", help="Merge commit message")
@click.option("--strategy", default="merge_commit", help="Merge strategy (merge_commit, squash, fast_forward)")
@click.option("--close-branch", is_flag=True, help="Close source branch after merge")
@click.pass_context
@validate_auth
def merge(ctx, pr_id, message, strategy, close_branch):
    """Merge a pull request."""
    try:
        config = load_config()
        api = BitbucketAPI(config)
        
        workspace = ctx.obj["workspace"]
        repo = ctx.obj["repo"]
        
        if not workspace or not repo:
            repo_info = get_repository_info()
            workspace = workspace or repo_info["workspace"]
            repo = repo or repo_info["repo"]
        
        result = merge_pr(
            api, workspace, repo, pr_id,
            message=message,
            strategy=strategy,
            close_branch=close_branch
        )
        
        success(f"✓ PR #{pr_id} merged successfully")
        
        if ctx.obj["output_json"]:
            click.echo(json.dumps(result, indent=2))
        
    except Exception as e:
        error(f"Failed to merge PR: {e}")
        sys.exit(1)


@cli.command()
@click.argument("pr_id", type=int)
@click.option("--message", "-m", help="Comment message")
@click.option("--file", help="File path for inline comment")
@click.option("--line", type=int, help="Line number for inline comment")
@click.option("--from-line", type=int, help="Starting line for multi-line comment")
@click.option("--to-line", type=int, help="Ending line for multi-line comment")
@click.option("--reply-to", type=int, help="Reply to existing comment ID")
@click.pass_context
@validate_auth
def comment(ctx, pr_id, message, file, line, from_line, to_line, reply_to):
    """Add a comment to a pull request."""
    try:
        config = load_config()
        api = BitbucketAPI(config)
        
        workspace = ctx.obj["workspace"]
        repo = ctx.obj["repo"]
        
        if not workspace or not repo:
            repo_info = get_repository_info()
            workspace = workspace or repo_info["workspace"]
            repo = repo or repo_info["repo"]
        
        # Interactive mode if no message provided
        if not message:
            message = click.prompt("Comment")
        
        result = comment_pr(
            api, workspace, repo, pr_id,
            message=message,
            file=file,
            line=line,
            from_line=from_line,
            to_line=to_line,
            reply_to=reply_to
        )
        
        success(f"✓ Comment added to PR #{pr_id}")
        
        if ctx.obj["output_json"]:
            click.echo(json.dumps(result, indent=2))
        
    except Exception as e:
        error(f"Failed to add comment: {e}")
        sys.exit(1)


@cli.command()
@click.option("--repo-token", help="Set repository access token (recommended)")
@click.option("--username", help="Set Bitbucket username") 
@click.option("--app-password", help="Set app password")
@click.option("--oauth-token", help="Set OAuth token")
@click.option("--workspace", help="Set default workspace")
@click.option("--get", help="Get configuration value")
@click.option("--list", "list_config", is_flag=True, help="List all configuration")
@click.option("--reset", is_flag=True, help="Reset configuration to defaults")
def config(repo_token, username, app_password, oauth_token, workspace, get, list_config, reset):
    """Manage configuration settings."""
    try:
        if reset:
            from .auth import reset_config
            reset_config()
            success("Configuration reset to defaults")
            return
        
        if get:
            config = load_config()
            value = config
            for key in get.split("."):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    error(f"Configuration key '{get}' not found")
                    sys.exit(1)
            click.echo(value)
            return
        
        if list_config:
            config = load_config()
            # Hide sensitive information
            display_config = config.copy()
            if "auth" in display_config and "app_password" in display_config["auth"]:
                display_config["auth"]["app_password"] = "***hidden***"
            
            click.echo(json.dumps(display_config, indent=2))
            return
        
        # Set configuration values
        if any([repo_token, username, app_password, oauth_token, workspace]):
            from .auth import set_auth
            set_auth(
                repo_token=repo_token,
                username=username,
                app_password=app_password,
                oauth_token=oauth_token,
                workspace=workspace
            )
            success("Configuration updated successfully")
        else:
            # Interactive configuration - prefer repo token
            config = load_config()
            
            click.echo("Choose authentication method:")
            click.echo("1. Repository access token (recommended)")
            click.echo("2. Username + app password")
            
            auth_choice = click.prompt("Choice", type=click.Choice(['1', '2']), default='1')
            
            if auth_choice == '1':
                token = click.prompt("Repository access token", hide_input=True)
                workspace = click.prompt("Workspace", default=config["auth"].get("workspace", ""))
                
                from .auth import set_auth
                set_auth(repo_token=token, workspace=workspace)
            else:
                current_username = config["auth"].get("username", "")
                current_workspace = config["auth"].get("workspace", "")
                
                username = click.prompt("Username", default=current_username)
                password = click.prompt("App Password", hide_input=True)
                workspace = click.prompt("Workspace", default=current_workspace)
                
                from .auth import set_auth
                set_auth(username=username, app_password=password, workspace=workspace)
            
            success("Configuration saved successfully")
        
    except Exception as e:
        error(f"Configuration error: {e}")
        sys.exit(1)


def main():
    """Main entry point for the CLI application."""
    try:
        cli()
    except KeyboardInterrupt:
        error("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        error(f"Unexpected error: {e}")
        if "--verbose" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()