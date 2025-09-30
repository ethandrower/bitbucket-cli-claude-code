"""
ABOUTME: Update pull request properties like title, description, and reviewers
ABOUTME: Allows modification of existing PR details through Bitbucket API
"""

from typing import Dict, Any, Optional
from ..api import BitbucketAPI


def update_pr(
    api: BitbucketAPI,
    workspace: str,
    repo: str,
    pr_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    add_reviewer: Optional[str] = None,
    remove_reviewer: Optional[str] = None,
    dest: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update a pull request.
    
    Args:
        api: BitbucketAPI instance
        workspace: Bitbucket workspace name
        repo: Repository name
        pr_id: Pull request ID
        title: New title
        description: New description
        add_reviewer: Reviewer to add
        remove_reviewer: Reviewer to remove
        dest: New destination branch
        
    Returns:
        Updated pull request data
    """
    # Get current PR data
    pr_data = api.get_pull_request(workspace, repo, pr_id)
    
    # Handle reviewer changes
    reviewers = pr_data.get("reviewers", [])
    
    if add_reviewer:
        try:
            user_data = api.get_user(add_reviewer)
            reviewers.append({"uuid": user_data["uuid"]})
        except:
            reviewers.append({"username": add_reviewer})
    
    if remove_reviewer:
        reviewers = [r for r in reviewers if r.get("username") != remove_reviewer]
    
    return api.update_pull_request(
        workspace, repo, pr_id,
        title=title,
        description=description,
        destination_branch=dest,
        reviewers=reviewers if (add_reviewer or remove_reviewer) else None
    )