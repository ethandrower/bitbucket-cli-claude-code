"""
ABOUTME: Create pull request command implementation with template support and interactive mode
ABOUTME: Handles branch detection, reviewer resolution, and payload construction for Bitbucket API
"""

from typing import Optional, List, Dict, Any
import webbrowser
from pathlib import Path

from ..api import BitbucketAPI
from ..utils.git import get_current_branch
from ..utils.output import success, info, warning
from ..exceptions import ValidationError


def create_pr(
    api: BitbucketAPI,
    workspace: str,
    repo: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    source: Optional[str] = None,
    dest: Optional[str] = None,
    reviewers: Optional[str] = None,
    close_branch: bool = False,
    template: Optional[str] = None,
    web: bool = False
) -> Dict[str, Any]:
    """
    Create a new pull request.
    
    Args:
        api: BitbucketAPI instance
        workspace: Bitbucket workspace name
        repo: Repository name
        title: PR title
        description: PR description
        source: Source branch (defaults to current branch)
        dest: Destination branch (defaults to main)
        reviewers: Comma-separated list of reviewer usernames
        close_branch: Whether to close source branch when merged
        template: Path to PR template file
        web: Whether to open PR in web browser after creation
        
    Returns:
        Created pull request data
    """
    
    # Use template if provided
    if template:
        title, description = _load_template(template, title, description)
    
    # Auto-detect source branch if not provided
    if not source:
        try:
            source = get_current_branch()
            info(f"Using current branch: {source}")
        except Exception:
            raise ValidationError("Could not detect current branch. Please specify --source")
    
    # Use default destination if not provided
    if not dest:
        dest = api.config["defaults"]["default_branch"]
        info(f"Using default destination branch: {dest}")
    
    # Interactive title input if not provided
    if not title:
        import click
        title = click.prompt("PR Title", type=str)
    
    # Interactive description if not provided
    if not description:
        import click
        description = click.prompt("PR Description (optional)", default="", show_default=False)
    
    # Parse and resolve reviewers
    reviewer_list = []
    if reviewers:
        reviewer_names = [r.strip() for r in reviewers.split(",")]
        reviewer_list = _resolve_reviewers(api, reviewer_names)
    
    # Add default reviewers from config
    config_reviewers = api.config["defaults"].get("reviewers", [])
    if config_reviewers:
        config_reviewer_list = _resolve_reviewers(api, config_reviewers)
        reviewer_list.extend(config_reviewer_list)
        
        # Remove duplicates
        seen_uuids = set()
        unique_reviewers = []
        for reviewer in reviewer_list:
            uuid = reviewer.get("uuid")
            if uuid and uuid not in seen_uuids:
                unique_reviewers.append(reviewer)
                seen_uuids.add(uuid)
            elif not uuid and reviewer.get("username"):
                unique_reviewers.append(reviewer)
        
        reviewer_list = unique_reviewers
    
    # Create the pull request
    pr_data = api.create_pull_request(
        workspace=workspace,
        repo=repo,
        title=title,
        description=description,
        source_branch=source,
        destination_branch=dest,
        reviewers=reviewer_list,
        close_source_branch=close_branch or api.config["defaults"]["delete_source_branch"]
    )
    
    success(f"✓ Pull request #{pr_data['id']} created successfully")
    
    if web and pr_data.get("links", {}).get("html", {}).get("href"):
        webbrowser.open(pr_data["links"]["html"]["href"])
        info("Opened PR in web browser")
    
    return pr_data


def _load_template(template_path: str, title: Optional[str], description: Optional[str]) -> tuple[str, str]:
    """Load PR template from file."""
    try:
        path = Path(template_path)
        if not path.exists():
            raise ValidationError(f"Template file not found: {template_path}")
        
        content = path.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        
        # Simple template format: first line is title, rest is description
        template_title = lines[0].lstrip("# ").strip() if lines else ""
        template_description = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        
        return (
            title or template_title,
            description or template_description
        )
        
    except Exception as e:
        raise ValidationError(f"Failed to load template: {e}")


def _resolve_reviewers(api: BitbucketAPI, reviewer_names: List[str]) -> List[Dict[str, Any]]:
    """Resolve reviewer usernames to proper API format."""
    reviewers = []
    
    for username in reviewer_names:
        try:
            user_data = api.get_user(username)
            reviewers.append({"uuid": user_data["uuid"]})
            info(f"Added reviewer: {user_data.get('display_name', username)}")
        except Exception:
            warning(f"Could not find user '{username}', using username fallback")
            reviewers.append({"username": username})
    
    return reviewers


def validate_create_options(
    title: Optional[str] = None,
    source: Optional[str] = None,
    dest: Optional[str] = None,
    reviewers: Optional[str] = None
) -> None:
    """Validate create PR options."""
    errors = []
    
    if title and len(title.strip()) == 0:
        errors.append("Title cannot be empty")
    
    if source and not _is_valid_branch_name(source):
        errors.append(f"Invalid source branch name: {source}")
    
    if dest and not _is_valid_branch_name(dest):
        errors.append(f"Invalid destination branch name: {dest}")
    
    if reviewers:
        reviewer_list = [r.strip() for r in reviewers.split(",")]
        if any(not r for r in reviewer_list):
            errors.append("Invalid reviewers format. Use comma-separated usernames.")
    
    if errors:
        raise ValidationError("Validation errors:\n" + "\n".join(f"  - {e}" for e in errors))


def _is_valid_branch_name(branch_name: str) -> bool:
    """Validate branch name format."""
    import re
    # Basic Git branch name validation
    return bool(re.match(r"^[a-zA-Z0-9._/-]+$", branch_name) and not branch_name.startswith("-"))