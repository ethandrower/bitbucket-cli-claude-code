"""
ABOUTME: Merge pull request command with strategy selection and branch cleanup
ABOUTME: Supports different merge strategies (squash, merge_commit, fast_forward)
"""

from typing import Dict, Any, Optional
from ..api import BitbucketAPI


def merge_pr(
    api: BitbucketAPI,
    workspace: str,
    repo: str,
    pr_id: int,
    message: Optional[str] = None,
    strategy: str = "merge_commit",
    close_branch: bool = False
) -> Dict[str, Any]:
    """
    Merge a pull request.
    
    Args:
        api: BitbucketAPI instance
        workspace: Bitbucket workspace name
        repo: Repository name
        pr_id: Pull request ID
        message: Optional merge commit message
        strategy: Merge strategy (merge_commit, squash, fast_forward)
        close_branch: Whether to close source branch
        
    Returns:
        Merge result data
    """
    return api.merge_pull_request(
        workspace, repo, pr_id,
        message=message,
        merge_strategy=strategy,
        close_source_branch=close_branch
    )