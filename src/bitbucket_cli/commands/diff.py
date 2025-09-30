"""
ABOUTME: View pull request diff and diffstat information
ABOUTME: Retrieves and displays code changes for PR review
"""

from typing import Dict, Any, Optional
from ..api import BitbucketAPI


def diff_pr(
    api: BitbucketAPI,
    workspace: str,
    repo: str,
    pr_id: int,
    file: Optional[str] = None,
    stat: bool = False
) -> Any:
    """
    View diff for a pull request.
    
    Args:
        api: BitbucketAPI instance
        workspace: Bitbucket workspace name
        repo: Repository name
        pr_id: Pull request ID
        file: Specific file to show diff for
        stat: Show diffstat only
        
    Returns:
        Diff data (text or diffstat)
    """
    if stat:
        return api.get_diffstat(workspace, repo, pr_id)
    else:
        return api.get_diff(workspace, repo, pr_id)