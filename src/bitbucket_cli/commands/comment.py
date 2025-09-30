"""
ABOUTME: Add comments to pull requests with support for inline comments on specific lines
ABOUTME: Handles both general PR comments and file-specific inline comments with line numbers
"""

from typing import Dict, Any, Optional
from ..api import BitbucketAPI


def comment_pr(
    api: BitbucketAPI,
    workspace: str,
    repo: str,
    pr_id: int,
    message: str,
    file: Optional[str] = None,
    line: Optional[int] = None,
    from_line: Optional[int] = None,
    to_line: Optional[int] = None,
    reply_to: Optional[int] = None
) -> Dict[str, Any]:
    """
    Add a comment to a pull request.
    
    Args:
        api: BitbucketAPI instance
        workspace: Bitbucket workspace name
        repo: Repository name
        pr_id: Pull request ID
        message: Comment message
        file: File path for inline comment
        line: Line number for inline comment
        from_line: Starting line for multi-line comment
        to_line: Ending line for multi-line comment
        reply_to: Reply to existing comment ID
        
    Returns:
        Comment result data
    """
    return api.add_comment(
        workspace, repo, pr_id, message,
        file=file,
        line=line,
        from_line=from_line,
        to_line=to_line,
        reply_to=reply_to
    )