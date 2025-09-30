"""
ABOUTME: Show pull request details command with optional comment inclusion
ABOUTME: Displays comprehensive PR information and can open in web browser
"""

from typing import Dict, Any, Optional
import webbrowser
from ..api import BitbucketAPI


def show_pr(
    api: BitbucketAPI,
    workspace: str,
    repo: str,
    pr_id: int,
    web: bool = False,
    include_comments: bool = False
) -> Dict[str, Any]:
    """
    Show detailed pull request information.
    
    Args:
        api: BitbucketAPI instance
        workspace: Bitbucket workspace name
        repo: Repository name
        pr_id: Pull request ID
        web: Whether to open in web browser
        include_comments: Whether to include comments
        
    Returns:
        Pull request data with optional comments
    """
    pr_data = api.get_pull_request(workspace, repo, pr_id)
    
    if include_comments:
        comments = api.get_comments(workspace, repo, pr_id)
        pr_data["comments"] = comments
    
    if web and pr_data.get("links", {}).get("html", {}).get("href"):
        webbrowser.open(pr_data["links"]["html"]["href"])
    
    return pr_data