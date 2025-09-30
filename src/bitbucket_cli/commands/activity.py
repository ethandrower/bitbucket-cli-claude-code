"""
ABOUTME: View pull request activity timeline including updates, approvals, and comments
ABOUTME: Provides chronological view of all PR interactions and state changes
"""

from typing import List, Dict, Any
from ..api import BitbucketAPI


def activity_pr(
    api: BitbucketAPI,
    workspace: str,
    repo: str,
    pr_id: int,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    View activity timeline for a pull request.
    
    Args:
        api: BitbucketAPI instance
        workspace: Bitbucket workspace name
        repo: Repository name
        pr_id: Pull request ID
        limit: Number of activities to show
        
    Returns:
        List of activity data
    """
    activities = api.get_activity(workspace, repo, pr_id)
    
    # Limit results if specified
    if limit and len(activities) > limit:
        activities = activities[:limit]
    
    return activities