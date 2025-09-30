"""
ABOUTME: List pull requests command with filtering, pagination, and output formatting
ABOUTME: Supports state filtering, author/reviewer filters, and both JSON and table output
"""

from typing import List, Dict, Any, Optional
from ..api import BitbucketAPI


def list_prs(
    api: BitbucketAPI,
    workspace: str,
    repo: str,
    state: str = "OPEN",
    author: Optional[str] = None,
    reviewer: Optional[str] = None,
    limit: int = 25,
    fetch_all: bool = False
) -> List[Dict[str, Any]]:
    """
    List pull requests with filtering options.
    
    Args:
        api: BitbucketAPI instance
        workspace: Bitbucket workspace name
        repo: Repository name
        state: PR state filter (OPEN, MERGED, DECLINED, SUPERSEDED)
        author: Filter by author username
        reviewer: Filter by reviewer username
        limit: Number of results per page
        fetch_all: Whether to fetch all pages
        
    Returns:
        List of pull request data
    """
    
    return api.list_pull_requests(
        workspace=workspace,
        repo=repo,
        state=state,
        author=author,
        reviewer=reviewer,
        limit=limit,
        fetch_all=fetch_all
    )