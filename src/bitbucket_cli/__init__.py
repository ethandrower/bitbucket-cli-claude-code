"""
ABOUTME: Bitbucket CLI for Claude Code - Python package initialization
ABOUTME: Provides programmatic access to Bitbucket Cloud API for pull request management

Lightweight Python CLI tool for managing Bitbucket Cloud pull requests using REST API v2.0.
Designed specifically for integration with Claude Code workflows and automated PR reviews.
"""

__version__ = "1.0.0"
__author__ = "CiteMed Development Team"
__email__ = "dev@citemed.com"

from .api import BitbucketAPI
from .auth import load_config, save_config
from .models import PullRequest, Comment, User

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "BitbucketAPI",
    "load_config",
    "save_config", 
    "PullRequest",
    "Comment",
    "User",
]