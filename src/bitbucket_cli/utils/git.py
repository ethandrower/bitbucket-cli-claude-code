"""
ABOUTME: Git repository utilities for branch detection and repository information extraction
ABOUTME: Provides functions to interact with Git repositories for CLI context detection
"""

import os
import re
from pathlib import Path
from typing import Dict, Optional
from git import Repo, InvalidGitRepositoryError
from ..exceptions import GitError


def is_git_repository(path: Optional[str] = None) -> bool:
    """Check if the current directory (or specified path) is a Git repository."""
    try:
        if path:
            Repo(path)
        else:
            Repo()
        return True
    except InvalidGitRepositoryError:
        return False


def get_current_branch(repo_path: Optional[str] = None) -> str:
    """Get the current Git branch name."""
    try:
        repo = Repo(repo_path) if repo_path else Repo()
        
        if repo.head.is_detached:
            # Return commit hash if in detached HEAD state
            return repo.head.commit.hexsha[:8]
        
        return repo.active_branch.name
        
    except InvalidGitRepositoryError:
        raise GitError("Not in a Git repository")
    except Exception as e:
        raise GitError(f"Failed to get current branch: {e}")


def get_repository_info(repo_path: Optional[str] = None) -> Dict[str, str]:
    """
    Extract repository workspace and name from Git remote URL.
    
    Returns:
        Dict with 'workspace' and 'repo' keys
    """
    try:
        repo = Repo(repo_path) if repo_path else Repo()
        
        # Try to get remote URL from 'origin'
        if 'origin' in repo.remotes:
            remote_url = repo.remotes.origin.url
        elif repo.remotes:
            # Use first available remote
            remote_url = list(repo.remotes)[0].url
        else:
            raise GitError("No Git remotes found")
        
        return parse_git_remote_url(remote_url)
        
    except InvalidGitRepositoryError:
        raise GitError("Not in a Git repository")
    except Exception as e:
        raise GitError(f"Failed to get repository info: {e}")


def parse_git_remote_url(remote_url: str) -> Dict[str, str]:
    """
    Parse Git remote URL to extract Bitbucket workspace and repository name.
    
    Supports both SSH and HTTPS formats:
    - git@bitbucket.org:workspace/repo.git
    - https://bitbucket.org/workspace/repo.git
    - https://username@bitbucket.org/workspace/repo.git
    """
    
    # SSH format: git@bitbucket.org:workspace/repo.git
    ssh_pattern = r"git@bitbucket\.org:([^/]+)/([^/]+?)(?:\.git)?$"
    ssh_match = re.match(ssh_pattern, remote_url)
    
    if ssh_match:
        workspace, repo = ssh_match.groups()
        return {"workspace": workspace, "repo": repo}
    
    # HTTPS format: https://[username@]bitbucket.org/workspace/repo[.git]
    https_pattern = r"https://(?:[^@]+@)?bitbucket\.org/([^/]+)/([^/]+?)(?:\.git)?/?$"
    https_match = re.match(https_pattern, remote_url)
    
    if https_match:
        workspace, repo = https_match.groups()
        return {"workspace": workspace, "repo": repo}
    
    raise GitError(f"Could not parse Bitbucket remote URL: {remote_url}")


def get_git_root(repo_path: Optional[str] = None) -> Path:
    """Get the root directory of the Git repository."""
    try:
        repo = Repo(repo_path) if repo_path else Repo()
        return Path(repo.working_dir)
    except InvalidGitRepositoryError:
        raise GitError("Not in a Git repository")


def get_remote_branches(repo_path: Optional[str] = None) -> list[str]:
    """Get list of remote branch names."""
    try:
        repo = Repo(repo_path) if repo_path else Repo()
        
        remote_branches = []
        for remote in repo.remotes:
            for ref in remote.refs:
                # Extract branch name from refs/remotes/origin/branch_name
                branch_name = ref.name.split('/')[-1]
                if branch_name not in ['HEAD']:
                    remote_branches.append(branch_name)
        
        return list(set(remote_branches))  # Remove duplicates
        
    except InvalidGitRepositoryError:
        raise GitError("Not in a Git repository")
    except Exception as e:
        raise GitError(f"Failed to get remote branches: {e}")


def get_local_branches(repo_path: Optional[str] = None) -> list[str]:
    """Get list of local branch names."""
    try:
        repo = Repo(repo_path) if repo_path else Repo()
        return [branch.name for branch in repo.branches]
        
    except InvalidGitRepositoryError:
        raise GitError("Not in a Git repository")
    except Exception as e:
        raise GitError(f"Failed to get local branches: {e}")


def is_clean_working_directory(repo_path: Optional[str] = None) -> bool:
    """Check if the working directory is clean (no uncommitted changes)."""
    try:
        repo = Repo(repo_path) if repo_path else Repo()
        return not repo.is_dirty()
        
    except InvalidGitRepositoryError:
        raise GitError("Not in a Git repository")
    except Exception as e:
        raise GitError(f"Failed to check working directory status: {e}")


def get_commit_info(commit_hash: Optional[str] = None, repo_path: Optional[str] = None) -> Dict[str, str]:
    """Get information about a specific commit (or HEAD if not specified)."""
    try:
        repo = Repo(repo_path) if repo_path else Repo()
        
        if commit_hash:
            commit = repo.commit(commit_hash)
        else:
            commit = repo.head.commit
        
        return {
            "hash": commit.hexsha,
            "short_hash": commit.hexsha[:8],
            "message": commit.message.strip(),
            "author": f"{commit.author.name} <{commit.author.email}>",
            "date": commit.committed_datetime.isoformat()
        }
        
    except InvalidGitRepositoryError:
        raise GitError("Not in a Git repository")
    except Exception as e:
        raise GitError(f"Failed to get commit info: {e}")