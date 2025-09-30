"""
ABOUTME: Decline pull request command implementation
ABOUTME: Handles PR decline operation with optional message through Bitbucket API
"""

from typing import Dict, Any, Optional
from ..api import BitbucketAPI


def decline_pr(
    api: BitbucketAPI,
    workspace: str,
    repo: str,
    pr_id: int,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Decline a pull request.
    
    Args:
        api: BitbucketAPI instance
        workspace: Bitbucket workspace name
        repo: Repository name
        pr_id: Pull request ID
        message: Optional decline message
        
    Returns:
        Decline result data
    """
    return api.decline_pull_request(workspace, repo, pr_id, message=message)