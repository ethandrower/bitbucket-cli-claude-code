"""
ABOUTME: Pydantic data models for Bitbucket API objects with validation and serialization
ABOUTME: Provides type-safe representations of pull requests, comments, users, and other API entities
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class User(BaseModel):
    """Bitbucket user model."""
    username: str
    display_name: Optional[str] = None
    uuid: Optional[str] = None
    account_id: Optional[str] = None
    
    class Config:
        extra = "allow"


class Branch(BaseModel):
    """Git branch model."""
    name: str
    
    class Config:
        extra = "allow"


class Repository(BaseModel):
    """Repository model."""
    name: str
    full_name: str
    uuid: Optional[str] = None
    
    class Config:
        extra = "allow"


class PullRequestSource(BaseModel):
    """Pull request source information."""
    branch: Branch
    repository: Optional[Repository] = None
    commit: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"


class PullRequestDestination(BaseModel):
    """Pull request destination information."""
    branch: Branch
    repository: Optional[Repository] = None
    commit: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"


class PullRequestLinks(BaseModel):
    """Pull request links."""
    self: Optional[Dict[str, str]] = None
    html: Optional[Dict[str, str]] = None
    commits: Optional[Dict[str, str]] = None
    approve: Optional[Dict[str, str]] = None
    
    class Config:
        extra = "allow"


class PullRequest(BaseModel):
    """Pull request model."""
    id: int
    title: str
    description: Optional[str] = ""
    state: str = Field(..., pattern="^(OPEN|MERGED|DECLINED|SUPERSEDED)$")
    author: User
    source: PullRequestSource
    destination: PullRequestDestination
    reviewers: List[User] = []
    participants: List[User] = []
    links: Optional[PullRequestLinks] = None
    created_on: Optional[datetime] = None
    updated_on: Optional[datetime] = None
    merge_commit: Optional[Dict[str, Any]] = None
    close_source_branch: Optional[bool] = False
    
    @validator('created_on', 'updated_on', pre=True)
    def parse_datetime(cls, v):
        if isinstance(v, str):
            # Handle Bitbucket's ISO format with timezone
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                return datetime.fromisoformat(v)
        return v
    
    class Config:
        extra = "allow"


class CommentContent(BaseModel):
    """Comment content model."""
    raw: str
    markup: str = "markdown"
    html: Optional[str] = None
    
    class Config:
        extra = "allow"


class InlineCommentLocation(BaseModel):
    """Inline comment location."""
    path: str
    line: Optional[int] = None
    
    class Config:
        extra = "allow"


class InlineComment(BaseModel):
    """Inline comment positioning."""
    to: Optional[InlineCommentLocation] = None
    from_: Optional[InlineCommentLocation] = Field(None, alias="from")
    
    class Config:
        extra = "allow"
        validate_by_name = True


class Comment(BaseModel):
    """Comment model."""
    id: int
    content: CommentContent
    user: User
    created_on: Optional[datetime] = None
    updated_on: Optional[datetime] = None
    inline: Optional[InlineComment] = None
    parent: Optional[Dict[str, Any]] = None
    links: Optional[Dict[str, Any]] = None
    
    @validator('created_on', 'updated_on', pre=True)
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                return datetime.fromisoformat(v)
        return v
    
    class Config:
        extra = "allow"


class DiffStat(BaseModel):
    """Diff statistics for a file."""
    type: str
    status: str
    lines_added: int
    lines_removed: int
    old: Optional[Dict[str, Any]] = None
    new: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"


class Activity(BaseModel):
    """Activity/timeline entry."""
    update: Optional[Dict[str, Any]] = None
    approval: Optional[Dict[str, Any]] = None
    comment: Optional[Comment] = None
    
    class Config:
        extra = "allow"


class MergeResult(BaseModel):
    """Merge operation result."""
    type: str = "commit"
    hash: Optional[str] = None
    message: Optional[str] = None
    
    class Config:
        extra = "allow"


# Helper functions for model creation

def create_pull_request_from_api(data: Dict[str, Any]) -> PullRequest:
    """Create PullRequest model from API response data."""
    return PullRequest.parse_obj(data)


def create_comment_from_api(data: Dict[str, Any]) -> Comment:
    """Create Comment model from API response data."""
    return Comment.parse_obj(data)


def create_user_from_api(data: Dict[str, Any]) -> User:
    """Create User model from API response data."""
    return User.parse_obj(data)