"""
ABOUTME: Core API client for Bitbucket Cloud REST API v2.0 with comprehensive error handling
ABOUTME: Provides high-level methods for PR operations, pagination, and authentication management
"""

import time
from typing import Dict, List, Any, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .auth import get_auth_headers, get_workspace
from .exceptions import (
    BitbucketAPIError, 
    AuthenticationError, 
    NotFoundError, 
    PermissionError,
    RateLimitError,
    ConflictError
)
from .models import PullRequest, Comment, User


class BitbucketAPI:
    """
    Bitbucket Cloud REST API v2.0 client with comprehensive error handling and pagination.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config["api"]["base_url"].rstrip("/")
        self.timeout = config["api"]["timeout"]
        self.max_retries = config["api"]["retries"]
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for requests."""
        return get_auth_headers(self.config)
    
    def _handle_response(self, response: requests.Response) -> Any:
        """Handle API response and errors."""
        if response.status_code == 200 or response.status_code == 201:
            return response.json() if response.content else {}
        elif response.status_code == 204:
            return {}
        elif response.status_code == 401:
            raise AuthenticationError("Authentication failed. Check your credentials.")
        elif response.status_code == 403:
            raise PermissionError("Insufficient permissions for this operation.")
        elif response.status_code == 404:
            raise NotFoundError("Resource not found.")
        elif response.status_code == 409:
            raise ConflictError("Conflict - operation cannot be completed (e.g., PR already merged).")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded. Please wait and try again.")
        else:
            try:
                error_data = response.json()
                message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            except:
                message = f"HTTP {response.status_code}: {response.reason}"
            
            raise BitbucketAPIError(f"API Error: {message}")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make an authenticated request to the API."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        
        response = self.session.request(
            method=method,
            url=url,
            headers=headers,
            timeout=self.timeout,
            **kwargs
        )
        
        return self._handle_response(response)
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """Make a GET request."""
        return self._request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None) -> Any:
        """Make a POST request."""
        kwargs = {}
        if data:
            kwargs["data"] = data
        if json:
            kwargs["json"] = json
        return self._request("POST", endpoint, **kwargs)
    
    def put(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None) -> Any:
        """Make a PUT request."""
        kwargs = {}
        if data:
            kwargs["data"] = data
        if json:
            kwargs["json"] = json
        return self._request("PUT", endpoint, **kwargs)
    
    def delete(self, endpoint: str) -> Any:
        """Make a DELETE request."""
        return self._request("DELETE", endpoint)
    
    def get_all_pages(self, endpoint: str, params: Optional[Dict] = None) -> List[Any]:
        """Get all pages of paginated results."""
        results = []
        url = endpoint
        is_first_request = True
        
        while url:
            if is_first_request:
                response = self.get(url, params)
                is_first_request = False
            else:
                # For subsequent requests, url already contains the full URL
                parsed_url = url.replace(self.base_url, "")
                response = self.get(parsed_url)
            
            if "values" in response:
                results.extend(response["values"])
            
            # Get next page URL
            url = response.get("next")
            
            # Optional delay to respect rate limits
            if url:
                time.sleep(0.1)
        
        return results
    
    def get_paginated(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Get a single page of paginated results with pagination info."""
        response = self.get(endpoint, params)
        
        return {
            "values": response.get("values", []),
            "page": response.get("page", 1),
            "pagelen": response.get("pagelen", 10),
            "size": response.get("size", 0),
            "next": response.get("next"),
            "previous": response.get("previous")
        }
    
    # Pull Request Methods
    
    def create_pull_request(self, workspace: str, repo: str, **kwargs) -> Dict[str, Any]:
        """Create a new pull request."""
        endpoint = f"/repositories/{workspace}/{repo}/pullrequests"
        
        payload = {
            "title": kwargs.get("title"),
            "description": kwargs.get("description", ""),
            "source": {
                "branch": {"name": kwargs.get("source_branch")}
            },
            "destination": {
                "branch": {"name": kwargs.get("destination_branch", "main")}
            }
        }
        
        if kwargs.get("close_source_branch"):
            payload["close_source_branch"] = True
        
        if kwargs.get("reviewers"):
            payload["reviewers"] = kwargs["reviewers"]
        
        return self.post(endpoint, json=payload)
    
    def get_pull_request(self, workspace: str, repo: str, pr_id: int) -> Dict[str, Any]:
        """Get a specific pull request."""
        endpoint = f"/repositories/{workspace}/{repo}/pullrequests/{pr_id}"
        return self.get(endpoint)
    
    def list_pull_requests(self, workspace: str, repo: str, **kwargs) -> List[Dict[str, Any]]:
        """List pull requests with optional filtering."""
        endpoint = f"/repositories/{workspace}/{repo}/pullrequests"
        
        params = {}
        if kwargs.get("state"):
            params["state"] = kwargs["state"]
        if kwargs.get("limit"):
            params["pagelen"] = kwargs["limit"]
        
        # Build query string for additional filters
        query_parts = []
        if kwargs.get("author"):
            query_parts.append(f'author.username="{kwargs["author"]}"')
        if kwargs.get("reviewer"):
            query_parts.append(f'reviewers.username="{kwargs["reviewer"]}"')
        
        if query_parts:
            params["q"] = " AND ".join(query_parts)
        
        if kwargs.get("fetch_all"):
            return self.get_all_pages(endpoint, params)
        else:
            response = self.get_paginated(endpoint, params)
            return response["values"]
    
    def update_pull_request(self, workspace: str, repo: str, pr_id: int, **kwargs) -> Dict[str, Any]:
        """Update a pull request."""
        endpoint = f"/repositories/{workspace}/{repo}/pullrequests/{pr_id}"
        
        payload = {}
        if kwargs.get("title"):
            payload["title"] = kwargs["title"]
        if kwargs.get("description") is not None:
            payload["description"] = kwargs["description"]
        if kwargs.get("destination_branch"):
            payload["destination"] = {"branch": {"name": kwargs["destination_branch"]}}
        if kwargs.get("reviewers"):
            payload["reviewers"] = kwargs["reviewers"]
        
        return self.put(endpoint, json=payload)
    
    def approve_pull_request(self, workspace: str, repo: str, pr_id: int) -> Dict[str, Any]:
        """Approve a pull request."""
        endpoint = f"/repositories/{workspace}/{repo}/pullrequests/{pr_id}/approve"
        return self.post(endpoint)
    
    def unapprove_pull_request(self, workspace: str, repo: str, pr_id: int) -> Dict[str, Any]:
        """Remove approval from a pull request."""
        endpoint = f"/repositories/{workspace}/{repo}/pullrequests/{pr_id}/approve"
        return self.delete(endpoint)
    
    def decline_pull_request(self, workspace: str, repo: str, pr_id: int, message: Optional[str] = None) -> Dict[str, Any]:
        """Decline a pull request."""
        endpoint = f"/repositories/{workspace}/{repo}/pullrequests/{pr_id}/decline"
        payload = {}
        if message:
            payload["message"] = message
        return self.post(endpoint, json=payload)
    
    def merge_pull_request(self, workspace: str, repo: str, pr_id: int, **kwargs) -> Dict[str, Any]:
        """Merge a pull request."""
        endpoint = f"/repositories/{workspace}/{repo}/pullrequests/{pr_id}/merge"
        
        payload = {}
        if kwargs.get("message"):
            payload["message"] = kwargs["message"]
        if kwargs.get("close_source_branch"):
            payload["close_source_branch"] = True
        if kwargs.get("merge_strategy"):
            payload["merge_strategy"] = kwargs["merge_strategy"]
        
        return self.post(endpoint, json=payload)
    
    # Comment Methods
    
    def add_comment(self, workspace: str, repo: str, pr_id: int, message: str, **kwargs) -> Dict[str, Any]:
        """Add a comment to a pull request."""
        endpoint = f"/repositories/{workspace}/{repo}/pullrequests/{pr_id}/comments"
        
        payload = {
            "content": {
                "raw": message
            }
        }
        
        # Handle inline comments
        if kwargs.get("file"):
            inline = {"to": {"path": kwargs["file"]}}
            
            if kwargs.get("line"):
                inline["to"]["line"] = kwargs["line"]
            
            if kwargs.get("from_line") and kwargs.get("to_line"):
                inline["from"] = {"path": kwargs["file"], "line": kwargs["from_line"]}
                inline["to"]["line"] = kwargs["to_line"]
            
            payload["inline"] = inline
        
        # Handle reply to existing comment
        if kwargs.get("reply_to"):
            payload["parent"] = {"id": kwargs["reply_to"]}
        
        return self.post(endpoint, json=payload)
    
    def get_comments(self, workspace: str, repo: str, pr_id: int) -> List[Dict[str, Any]]:
        """Get all comments for a pull request."""
        endpoint = f"/repositories/{workspace}/{repo}/pullrequests/{pr_id}/comments"
        return self.get_all_pages(endpoint)
    
    # Utility Methods
    
    def get_diff(self, workspace: str, repo: str, pr_id: int) -> str:
        """Get the diff for a pull request."""
        endpoint = f"/repositories/{workspace}/{repo}/pullrequests/{pr_id}/diff"
        
        # This endpoint returns raw diff text, not JSON
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        headers["Accept"] = "text/plain"
        
        response = self.session.get(url, headers=headers, timeout=self.timeout)
        
        if response.status_code == 200:
            return response.text
        else:
            self._handle_response(response)
    
    def get_diffstat(self, workspace: str, repo: str, pr_id: int) -> Dict[str, Any]:
        """Get diffstat for a pull request."""
        endpoint = f"/repositories/{workspace}/{repo}/pullrequests/{pr_id}/diffstat"
        return self.get(endpoint)
    
    def get_activity(self, workspace: str, repo: str, pr_id: int) -> List[Dict[str, Any]]:
        """Get activity timeline for a pull request."""
        endpoint = f"/repositories/{workspace}/{repo}/pullrequests/{pr_id}/activity"
        return self.get_all_pages(endpoint)
    
    def get_user(self, username: str) -> Dict[str, Any]:
        """Get user information."""
        endpoint = f"/users/{username}"
        return self.get(endpoint)
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get current authenticated user information."""
        endpoint = "/user"
        return self.get(endpoint)
    
    def test_connection(self) -> Dict[str, Any]:
        """Test API connection and authentication."""
        try:
            user = self.get_current_user()
            return {
                "success": True,
                "user": {
                    "username": user.get("username"),
                    "display_name": user.get("display_name"),
                    "uuid": user.get("uuid")
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }