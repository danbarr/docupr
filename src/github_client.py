"""
GitHub client module for DocuPR.

This module handles GitHub authentication and API interactions.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import aiohttp
from github import Github, Auth
from github.PullRequest import PullRequest
from github.Repository import Repository

from .config import get_github_config

logger = logging.getLogger(__name__)

class GitHubClient:
    """
    Client for interacting with the GitHub API.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the GitHub client.
        
        Args:
            token (Optional[str]): GitHub Personal Access Token. If not provided, will use from config.
        """
        self.token = token
        self.github = None
        self.config = get_github_config()
        
    async def authenticate(self) -> str:
        """
        Get the GitHub authentication token.
        
        Returns:
            str: GitHub Personal Access Token
        """
        if self.token:
            return self.token
            
        token = self.config["token"]
        
        if not token:
            raise ValueError("GitHub Personal Access Token is required for authentication. "
                            "Please set the GITHUB_TOKEN environment variable.")
            
        self.token = token
        return self.token
    
    def initialize_client(self) -> None:
        """
        Initialize the GitHub client with the authenticated token.
        """
        if not self.token:
            raise ValueError("GitHub token is required. Call authenticate() first.")
            
        # Use the newer Auth.Token method instead of passing the token directly
        auth = Auth.Token(self.token)
        self.github = Github(auth=auth, base_url=self.config["api_url"])
    
    def get_repository(self, repo_url: str) -> Repository:
        """
        Get a GitHub repository by URL.
        
        Args:
            repo_url (str): GitHub repository URL
            
        Returns:
            Repository: GitHub repository object
        """
        if not self.github:
            self.initialize_client()
            
        # Extract owner and repo name from URL
        # Handle formats like:
        # - https://github.com/owner/repo
        # - github.com/owner/repo
        # - owner/repo
        parts = repo_url.strip("/").split("/")
        if "github.com" in parts:
            idx = parts.index("github.com")
            if len(parts) > idx + 2:
                owner, repo = parts[idx + 1], parts[idx + 2]
            else:
                raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
        elif len(parts) == 2:
            owner, repo = parts
        else:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
            
        # Remove .git suffix if present
        if repo.endswith(".git"):
            repo = repo[:-4]
            
        return self.github.get_repo(f"{owner}/{repo}")
    
    async def get_release_date(self, repo: Repository, tag: Optional[str] = None) -> Optional[datetime]:
        """
        Get the date of a specific release or the latest release for a repository.
        
        Args:
            repo (Repository): GitHub repository object
            tag (Optional[str]): Release tag to get the date for. If None, get the latest release.
            
        Returns:
            Optional[datetime]: Date of the release, or None if no releases
        """
        try:
            if tag:
                logger.info(f"Looking for release with tag: {tag}")
                try:
                    release = repo.get_release(tag)
                    logger.info(f"Found release with tag {tag} created at {release.created_at}")
                    return release.created_at
                except Exception as e:
                    logger.warning(f"Failed to get release with tag {tag}: {e}")
                    logger.info("Falling back to latest release")
                    # Fall back to latest release if tag not found
            
            # Get latest release if no tag specified or tag not found
            releases = repo.get_releases()
            if releases.totalCount > 0:
                latest_release = releases[0]
                logger.info(f"Using latest release created at {latest_release.created_at}")
                return latest_release.created_at
                
            logger.warning("No releases found")
            return None
        except Exception as e:
            logger.warning(f"Failed to get release: {e}")
            return None
    
    async def get_prs_since_date(
        self, repo: Repository, since_date: Optional[datetime] = None
    ) -> List[PullRequest]:
        """
        Get pull requests merged since a specific date.
        
        Args:
            repo (Repository): GitHub repository object
            since_date (Optional[datetime]): Date to filter PRs by
            
        Returns:
            List[PullRequest]: List of pull requests
        """
        if not since_date:
            # Default to 30 days ago if no date provided
            since_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            since_date = since_date.replace(
                day=max(1, since_date.day - 30)
            )
        
        logger.info(f"Fetching PRs merged after {since_date}")
        
        # Use GitHub's search API to find PRs more efficiently
        # This is much faster than iterating through all PRs
        query = f"repo:{repo.full_name} is:pr is:merged merged:>={since_date.strftime('%Y-%m-%d')}"
        logger.info(f"Using search query: {query}")
        
        # Get merged PRs since the date using search
        prs_search = self.github.search_issues(query)
        result = []
        
        # Limit to first 100 PRs for performance
        max_prs = 100
        count = 0
        
        for issue in prs_search:
            if count >= max_prs:
                logger.info(f"Reached limit of {max_prs} PRs, stopping search")
                break
                
            # Convert issue to PR
            pr_number = issue.number
            pr = repo.get_pull(pr_number)
            
            # Check if PR is merged
            if pr.merged and pr.merged_at:
                # Convert the date string to a date object for comparison
                # This handles the timezone issue by using only the date part
                pr_date = pr.merged_at.date()
                since_date_only = since_date.date()
                
                if pr_date >= since_date_only:
                    result.append(pr)
                    count += 1
                
        logger.info(f"Found {len(result)} PRs merged after {since_date}")
        return result
    
    async def get_pr_diff(self, pr: PullRequest) -> str:
        """
        Get the diff for a pull request.
        
        Args:
            pr (PullRequest): GitHub pull request object
            
        Returns:
            str: Pull request diff
        """
        if not self.token:
            raise ValueError("GitHub token is required. Call authenticate() first.")
            
        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "Authorization": f"token {self.token}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(pr.diff_url, headers=headers) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise ValueError(f"Failed to get PR diff: {error_text}")
                    
                return await resp.text()
    
    async def get_pr_details(self, pr: PullRequest) -> Dict[str, Any]:
        """
        Get detailed information about a pull request.
        
        Args:
            pr (PullRequest): GitHub pull request object
            
        Returns:
            Dict[str, Any]: Pull request details
        """
        diff = await self.get_pr_diff(pr)
        
        return {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body or "",
            "url": pr.html_url,
            "author": pr.user.login if pr.user else "Unknown",
            "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
            "diff": diff,
            "changed_files": [f.filename for f in pr.get_files()]
        }
