"""
Tests for the GitHub client module.
"""

import asyncio
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest
import github
from github import Auth

from src.github_client import GitHubClient


class TestGitHubClient(unittest.TestCase):
    """
    Test cases for the GitHub client.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        self.client = GitHubClient(token="test_token")
        self.client.github = MagicMock()
        
    def test_initialize_client(self):
        """
        Test initializing the GitHub client.
        """
        # Reset the client to test initialization
        self.client.github = None
        
        # Initialize the client
        self.client.initialize_client()
        
        # Assert that the GitHub client was initialized
        self.assertIsNotNone(self.client.github)
        
    def test_get_repository_full_url(self):
        """
        Test getting a repository by full URL.
        """
        # Mock the get_repo method
        mock_repo = MagicMock()
        self.client.github.get_repo.return_value = mock_repo
        
        # Test with a full URL
        repo = self.client.get_repository("https://github.com/owner/repo")
        
        # Assert that get_repo was called with the correct arguments
        self.client.github.get_repo.assert_called_once_with("owner/repo")
        self.assertEqual(repo, mock_repo)
        
    def test_get_repository_short_url(self):
        """
        Test getting a repository by short URL.
        """
        # Mock the get_repo method
        mock_repo = MagicMock()
        self.client.github.get_repo.return_value = mock_repo
        
        # Test with a short URL
        repo = self.client.get_repository("owner/repo")
        
        # Assert that get_repo was called with the correct arguments
        self.client.github.get_repo.assert_called_once_with("owner/repo")
        self.assertEqual(repo, mock_repo)
        
    def test_get_repository_with_git_suffix(self):
        """
        Test getting a repository with .git suffix.
        """
        # Mock the get_repo method
        mock_repo = MagicMock()
        self.client.github.get_repo.return_value = mock_repo
        
        # Test with a URL that has a .git suffix
        repo = self.client.get_repository("https://github.com/owner/repo.git")
        
        # Assert that get_repo was called with the correct arguments
        self.client.github.get_repo.assert_called_once_with("owner/repo")
        self.assertEqual(repo, mock_repo)
        
    def test_get_repository_invalid_url(self):
        """
        Test getting a repository with an invalid URL.
        """
        # Test with an invalid URL
        with self.assertRaises(ValueError):
            self.client.get_repository("invalid_url")


@pytest.mark.asyncio
class TestGitHubClientAsync:
    """
    Async test cases for the GitHub client.
    """
    
    async def test_authenticate_with_token(self):
        """
        Test authenticating with GitHub using a provided token.
        """
        # Create a client with a mock token
        client = GitHubClient(token="test_token")
        
        # Authenticate with GitHub
        token = await client.authenticate()
        
        # Assert that the token is correct
        assert token == "test_token"
        
    async def test_authenticate_from_config(self):
        """
        Test authenticating with GitHub using a token from config.
        """
        # Create a client without a token
        client = GitHubClient()
        client.config = {"token": "config_token"}
        
        # Authenticate with GitHub
        token = await client.authenticate()
        
        # Assert that the token is correct
        assert token == "config_token"
        
    async def test_authenticate_no_token(self):
        """
        Test authenticating with GitHub with no token.
        """
        # Create a client without a token
        client = GitHubClient()
        client.config = {"token": None}
        
        # Authenticate with GitHub should raise an error
        with pytest.raises(ValueError):
            await client.authenticate()
    
    async def test_get_release_date(self):
        """
        Test getting the release date.
        """
        # Create a client with a mock token
        client = GitHubClient(token="test_token")
        client.github = MagicMock()
        
        # Mock the repository
        mock_repo = MagicMock()
        
        # Mock the releases
        mock_release = MagicMock()
        mock_release.created_at = datetime(2023, 1, 1)
        mock_releases = MagicMock()
        mock_releases.totalCount = 1
        mock_releases.__getitem__.return_value = mock_release
        mock_repo.get_releases.return_value = mock_releases
        
        # Get the release date
        release_date = await client.get_release_date(mock_repo)
        
        # Assert that the release date is correct
        assert release_date == datetime(2023, 1, 1)
        
    async def test_get_release_date_no_releases(self):
        """
        Test getting the release date when there are no releases.
        """
        # Create a client with a mock token
        client = GitHubClient(token="test_token")
        client.github = MagicMock()
        
        # Mock the repository
        mock_repo = MagicMock()
        
        # Mock the releases
        mock_releases = MagicMock()
        mock_releases.totalCount = 0
        mock_repo.get_releases.return_value = mock_releases
        
        # Get the release date
        release_date = await client.get_release_date(mock_repo)
        
        # Assert that the release date is None
        assert release_date is None
        
    async def test_get_release_date_with_tag(self):
        """
        Test getting the release date with a specific tag.
        """
        # Create a client with a mock token
        client = GitHubClient(token="test_token")
        client.github = MagicMock()
        
        # Mock the repository
        mock_repo = MagicMock()
        
        # Mock the release
        mock_release = MagicMock()
        mock_release.created_at = datetime(2023, 1, 1)
        mock_repo.get_release.return_value = mock_release
        
        # Get the release date with a tag
        release_date = await client.get_release_date(mock_repo, "v1.0.0")
        
        # Assert that the release date is correct
        assert release_date == datetime(2023, 1, 1)
        
    async def test_get_prs_since_date(self):
        """
        Test getting PRs since a specific date.
        """
        # Create a client with a mock token
        client = GitHubClient(token="test_token")
        client.github = MagicMock()
        
        # Mock the repository
        mock_repo = MagicMock()
        
        # Mock the search issues
        mock_issue1 = MagicMock()
        mock_issue1.number = 1
        
        mock_issue2 = MagicMock()
        mock_issue2.number = 2
        
        mock_issues = [mock_issue1, mock_issue2]
        client.github.search_issues.return_value = mock_issues
        
        # Mock the PRs with proper date objects
        mock_pr1 = MagicMock()
        mock_pr1.merged = True
        mock_merged_at1 = datetime(2023, 2, 1)
        # Mock the date() method to return a date object
        mock_pr1.merged_at = MagicMock()
        mock_pr1.merged_at.date.return_value = mock_merged_at1.date()
        
        mock_pr2 = MagicMock()
        mock_pr2.merged = True
        mock_merged_at2 = datetime(2023, 1, 15)
        # Mock the date() method to return a date object
        mock_pr2.merged_at = MagicMock()
        mock_pr2.merged_at.date.return_value = mock_merged_at2.date()
        
        # Mock the get_pull method
        mock_repo.get_pull.side_effect = lambda number: mock_pr1 if number == 1 else mock_pr2
        
        # Get PRs since a specific date
        since_date = datetime(2023, 1, 1)
        prs = await client.get_prs_since_date(mock_repo, since_date)
        
        # Assert that the correct PRs were returned
        assert len(prs) == 2
        
    @patch("aiohttp.ClientSession.get")
    async def test_get_pr_diff(self, mock_get):
        """
        Test getting a PR diff.
        """
        # Create a client with a mock token
        client = GitHubClient(token="test_token")
        
        # Mock the PR
        mock_pr = MagicMock()
        mock_pr.diff_url = "https://github.com/owner/repo/pull/1.diff"
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.status = 200
        
        # Use async_mock instead of coroutine
        async def mock_text():
            return "mock diff"
            
        mock_response.text = mock_text
        mock_response.__aenter__.return_value = mock_response
        
        # Mock the session
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        
        # Mock the ClientSession
        mock_get.return_value = mock_response
        
        # Get the PR diff
        diff = await client.get_pr_diff(mock_pr)
        
        # Assert that the diff is correct
        assert diff == "mock diff"
        
    async def test_get_pr_details(self):
        """
        Test getting PR details.
        """
        # Create a client with a mock token
        client = GitHubClient(token="test_token")
        
        # Mock the PR
        mock_pr = MagicMock()
        mock_pr.number = 1
        mock_pr.title = "Test PR"
        mock_pr.body = "Test body"
        mock_pr.html_url = "https://github.com/owner/repo/pull/1"
        mock_pr.user.login = "testuser"
        mock_pr.merged_at = datetime(2023, 1, 1)
        
        # Mock the files
        mock_file1 = MagicMock()
        mock_file1.filename = "file1.py"
        mock_file2 = MagicMock()
        mock_file2.filename = "file2.py"
        mock_pr.get_files.return_value = [mock_file1, mock_file2]
        
        # Mock the get_pr_diff method
        async def mock_get_pr_diff(pr):
            return "mock diff"
            
        client.get_pr_diff = mock_get_pr_diff
        
        # Get the PR details
        details = await client.get_pr_details(mock_pr)
        
        # Assert that the details are correct
        assert details["number"] == 1
        assert details["title"] == "Test PR"
        assert details["body"] == "Test body"
        assert details["url"] == "https://github.com/owner/repo/pull/1"
        assert details["author"] == "testuser"
        assert details["merged_at"] == "2023-01-01T00:00:00"
        assert details["diff"] == "mock diff"
        assert details["changed_files"] == ["file1.py", "file2.py"]


if __name__ == "__main__":
    unittest.main()
