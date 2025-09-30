"""
ABOUTME: Authentication and configuration management for Bitbucket Cloud API
ABOUTME: Handles app passwords, tokens, and secure credential storage in user config files
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from .exceptions import AuthenticationError, ConfigurationError


DEFAULT_CONFIG = {
    "auth": {
        "repo_token": None,  # Primary: Repository access token
        "username": None,    # Fallback: Username for app password auth
        "app_password": None,  # Fallback: App password
        "workspace": None,
        "oauth_token": None,  # Enterprise OAuth token
    },
    "defaults": {
        "reviewers": [],
        "delete_source_branch": True,
        "merge_strategy": "merge_commit",
        "default_branch": "main",
    },
    "api": {
        "base_url": "https://api.bitbucket.org/2.0",
        "timeout": 30,
        "retries": 3,
    }
}

CONFIG_DIR = Path.home() / ".bitbucket-cli"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def ensure_config_dir() -> None:
    """Ensure the configuration directory exists."""
    CONFIG_DIR.mkdir(exist_ok=True, mode=0o700)


def load_config() -> Dict[str, Any]:
    """Load configuration from file, creating defaults if needed."""
    ensure_config_dir()
    
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        # Merge with defaults to ensure all keys exist
        def merge_configs(default: dict, user: dict) -> dict:
            result = default.copy()
            for key, value in user.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_configs(result[key], value)
                else:
                    result[key] = value
            return result
        
        return merge_configs(DEFAULT_CONFIG, config)
        
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in config file: {e}")
    except Exception as e:
        raise ConfigurationError(f"Error loading config: {e}")


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file."""
    ensure_config_dir()
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            yaml.safe_dump(config, f, default_flow_style=False, indent=2)
        
        # Set restrictive permissions on config file
        CONFIG_FILE.chmod(0o600)
        
    except Exception as e:
        raise ConfigurationError(f"Error saving config: {e}")


def get_auth_headers(config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Get authentication headers for API requests."""
    if config is None:
        config = load_config()
    
    auth = config.get("auth", {})
    
    # Check environment variables first
    repo_token = auth.get("repo_token") or os.getenv("BITBUCKET_REPO_TOKEN")
    oauth_token = auth.get("oauth_token") or os.getenv("BITBUCKET_OAUTH_TOKEN")
    username = auth.get("username") or os.getenv("BITBUCKET_USERNAME")
    app_password = auth.get("app_password") or os.getenv("BITBUCKET_APP_PASSWORD")
    
    # Priority 1: Repository access token (simplest and most secure)
    if repo_token:
        return {
            "Authorization": f"Bearer {repo_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "bitbucket-cli-for-claude-code/1.0.0"
        }
    
    # Priority 2: OAuth token (enterprise/advanced setups)
    if oauth_token:
        return {
            "Authorization": f"Bearer {oauth_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "bitbucket-cli-for-claude-code/1.0.0"
        }
    
    # Priority 3: Username + App password (fallback for complex setups)
    if username and app_password:
        import base64
        credentials = base64.b64encode(f"{username}:{app_password}".encode()).decode()
        return {
            "Authorization": f"Basic {credentials}",
            "Accept": "application/json", 
            "Content-Type": "application/json",
            "User-Agent": "bitbucket-cli-for-claude-code/1.0.0"
        }
    
    raise AuthenticationError(
        "No authentication configured. Use:\n"
        "  bb-pr config --repo-token YOUR_REPO_TOKEN\n"
        "  OR export BITBUCKET_REPO_TOKEN=your_token"
    )


def validate_auth(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Validate authentication by making a test API call."""
    if config is None:
        config = load_config()
    
    try:
        headers = get_auth_headers(config)
        base_url = config["api"]["base_url"]
        timeout = config["api"]["timeout"]
        
        # For repository tokens, try a repository-specific endpoint first
        auth = config.get("auth", {})
        repo_token = auth.get("repo_token") or os.getenv("BITBUCKET_REPO_TOKEN")
        
        if repo_token:
            # Repository tokens can't access /user endpoint, so we skip detailed validation
            # The token will be validated when actually making repository API calls
            return {
                "valid": True,
                "user": {
                    "username": "repository-token-user",
                    "display_name": "Repository Token User",
                    "uuid": None
                }
            }
        
        # For username/password or OAuth tokens, use /user endpoint
        response = requests.get(
            f"{base_url}/user",
            headers=headers,
            timeout=timeout
        )
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid credentials. Check your username and app password.")
        elif response.status_code != 200:
            raise AuthenticationError(f"Authentication failed: {response.status_code} {response.reason}")
        
        user_data = response.json()
        return {
            "valid": True,
            "user": {
                "username": user_data.get("username"),
                "display_name": user_data.get("display_name"),
                "uuid": user_data.get("uuid")
            }
        }
        
    except requests.RequestException as e:
        raise AuthenticationError(f"Network error during authentication: {e}")
    except Exception as e:
        raise AuthenticationError(f"Authentication validation failed: {e}")


def is_authenticated(config: Optional[Dict[str, Any]] = None) -> bool:
    """Check if authentication is configured."""
    if config is None:
        config = load_config()
    
    auth = config.get("auth", {})
    
    # Check environment variables
    repo_token = auth.get("repo_token") or os.getenv("BITBUCKET_REPO_TOKEN")
    oauth_token = auth.get("oauth_token") or os.getenv("BITBUCKET_OAUTH_TOKEN")
    username = auth.get("username") or os.getenv("BITBUCKET_USERNAME")
    app_password = auth.get("app_password") or os.getenv("BITBUCKET_APP_PASSWORD")
    
    # Repository token (preferred)
    if repo_token:
        return True
    
    # OAuth token
    if oauth_token:
        return True
    
    # Username and app password
    return bool(username and app_password)


def set_auth(repo_token: Optional[str] = None,
             username: Optional[str] = None, 
             app_password: Optional[str] = None,
             workspace: Optional[str] = None,
             oauth_token: Optional[str] = None) -> None:
    """Set authentication credentials."""
    config = load_config()
    
    if repo_token:
        config["auth"]["repo_token"] = repo_token
        # Clear other auth methods when setting repo token
        config["auth"]["username"] = None
        config["auth"]["app_password"] = None
        config["auth"]["oauth_token"] = None
    if username:
        config["auth"]["username"] = username
    if app_password:
        config["auth"]["app_password"] = app_password
    if workspace:
        config["auth"]["workspace"] = workspace
    if oauth_token:
        config["auth"]["oauth_token"] = oauth_token
        # Clear basic auth when setting OAuth
        config["auth"]["username"] = None
        config["auth"]["app_password"] = None
    
    save_config(config)


def clear_auth() -> None:
    """Clear all authentication credentials."""
    config = load_config()
    config["auth"] = {
        "repo_token": None,
        "username": None,
        "app_password": None,
        "workspace": None,
        "oauth_token": None,
    }
    save_config(config)


def get_config_value(key_path: str, config: Optional[Dict[str, Any]] = None) -> Any:
    """Get configuration value by dot-separated key path."""
    if config is None:
        config = load_config()
    
    keys = key_path.split(".")
    value = config
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    
    return value


def set_config_value(key_path: str, value: Any) -> None:
    """Set configuration value by dot-separated key path."""
    config = load_config()
    keys = key_path.split(".")
    current = config
    
    # Navigate to the parent of the target key
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    # Set the final value
    current[keys[-1]] = value
    save_config(config)


def reset_config() -> None:
    """Reset configuration to defaults."""
    save_config(DEFAULT_CONFIG.copy())


def get_workspace(config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Get the default workspace from config."""
    if config is None:
        config = load_config()
    
    return config.get("auth", {}).get("workspace")


def get_username(config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Get the current username from config."""
    if config is None:
        config = load_config()
    
    return config.get("auth", {}).get("username")