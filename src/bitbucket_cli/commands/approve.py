"""
ABOUTME: Approve and unapprove pull request commands for review workflow
ABOUTME: Handles PR approval state changes through Bitbucket API endpoints
"""

from typing import Dict, Any
from ..api import BitbucketAPI


def approve_pr(api: BitbucketAPI, workspace: str, repo: str, pr_id: int) -> Dict[str, Any]:
    """
    Approve a pull request.
    
    Args:
        api: BitbucketAPI instance
        workspace: Bitbucket workspace name
        repo: Repository name
        pr_id: Pull request ID
        
    Returns:
        Approval result data
    """
    return api.approve_pull_request(workspace, repo, pr_id)


def unapprove_pr(api: BitbucketAPI, workspace: str, repo: str, pr_id: int) -> Dict[str, Any]:
    """
    Remove approval from a pull request.
    
    Args:
        api: BitbucketAPI instance
        workspace: Bitbucket workspace name
        repo: Repository name
        pr_id: Pull request ID
        
    Returns:
        Unapproval result data
    """
    return api.unapprove_pull_request(workspace, repo, pr_id)