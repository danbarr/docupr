"""
Tests for the OpenAI analyzer module.
"""

import json
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from src.openai_analyzer import OpenAIAnalyzer


@pytest.mark.asyncio
class TestOpenAIAnalyzer:
    """
    Test cases for the OpenAI analyzer.
    """
    
    async def test_analyze_pr_success(self):
        """
        Test analyzing a PR successfully.
        """
        # Create the analyzer
        analyzer = OpenAIAnalyzer()
        
        # Mock the rate limit method
        analyzer._rate_limit = AsyncMock()
        
        # Mock the _get_openai_response method
        analyzer._get_openai_response = AsyncMock(return_value=json.dumps({
            "user_facing": True,
            "docs_impact": {
                "update_existing": ["docs/api.md"],
                "create_new": ["docs/new-feature.md"],
                "suggested_content": ["Add section on new authentication flow"]
            },
            "reasoning": "This PR adds a new feature that users will interact with"
        }))
        
        # Analyze a PR
        pr_details = {
            "number": 1,
            "title": "Add new feature",
            "body": "This PR adds a new feature",
            "url": "https://github.com/owner/repo/pull/1",
            "author": "testuser",
            "merged_at": "2023-01-01T00:00:00",
            "diff": "mock diff",
            "changed_files": ["src/feature.py"]
        }
        
        result = await analyzer.analyze_pr(pr_details)
        
        # Assert that the result is correct
        assert result["user_facing"] is True
        assert "docs/api.md" in result["docs_impact"]["update_existing"]
        assert "docs/new-feature.md" in result["docs_impact"]["create_new"]
        assert "Add section on new authentication flow" in result["docs_impact"]["suggested_content"]
        assert result["pr_number"] == 1
        assert result["pr_title"] == "Add new feature"
        assert result["pr_url"] == "https://github.com/owner/repo/pull/1"
        
    async def test_analyze_pr_json_error(self):
        """
        Test analyzing a PR with a JSON error.
        """
        # Create the analyzer
        analyzer = OpenAIAnalyzer()
        
        # Mock the rate limit method
        analyzer._rate_limit = AsyncMock()
        
        # Mock the _get_openai_response method
        analyzer._get_openai_response = AsyncMock(return_value="This is not valid JSON")
        
        # Analyze a PR
        pr_details = {
            "number": 1,
            "title": "Add new feature",
            "body": "This PR adds a new feature",
            "url": "https://github.com/owner/repo/pull/1",
            "author": "testuser",
            "merged_at": "2023-01-01T00:00:00",
            "diff": "mock diff",
            "changed_files": ["src/feature.py"]
        }
        
        result = await analyzer.analyze_pr(pr_details)
        
        # Assert that the result contains default values
        assert "pr_number" in result
        assert "pr_title" in result
        assert "pr_url" in result
        assert "user_facing" in result
        assert "docs_impact" in result
        
    async def test_analyze_pr_api_error(self):
        """
        Test analyzing a PR with an API error.
        """
        # Create the analyzer
        analyzer = OpenAIAnalyzer()
        
        # Mock the rate limit method
        analyzer._rate_limit = AsyncMock()
        
        # Mock the _get_openai_response method to raise an exception
        analyzer._get_openai_response = AsyncMock(side_effect=Exception("API error"))
        
        # Analyze a PR
        pr_details = {
            "number": 1,
            "title": "Add new feature",
            "body": "This PR adds a new feature",
            "url": "https://github.com/owner/repo/pull/1",
            "author": "testuser",
            "merged_at": "2023-01-01T00:00:00",
            "diff": "mock diff",
            "changed_files": ["src/feature.py"]
        }
        
        result = await analyzer.analyze_pr(pr_details)
        
        # Assert that the result contains error information
        assert result["pr_number"] == 1
        assert result["pr_title"] == "Add new feature"
        assert result["pr_url"] == "https://github.com/owner/repo/pull/1"
        assert result["user_facing"] is False
        assert "error" in result
        assert "API error" in result["error"]
        
    async def test_analyze_pr_json_extraction(self):
        """
        Test analyzing a PR with JSON extraction.
        """
        # Create the analyzer
        analyzer = OpenAIAnalyzer()
        
        # Mock the rate limit method
        analyzer._rate_limit = AsyncMock()
        
        # Mock the _get_openai_response method
        analyzer._get_openai_response = AsyncMock(return_value="""
        Here's my analysis:
        
        ```json
        {
            "user_facing": true,
            "docs_impact": {
                "update_existing": ["docs/api.md"],
                "create_new": [],
                "suggested_content": []
            },
            "reasoning": "This PR updates the API"
        }
        ```
        """)
        
        # Analyze a PR
        pr_details = {
            "number": 1,
            "title": "Update API",
            "body": "This PR updates the API",
            "url": "https://github.com/owner/repo/pull/1",
            "author": "testuser",
            "merged_at": "2023-01-01T00:00:00",
            "diff": "mock diff",
            "changed_files": ["src/api.py"]
        }
        
        result = await analyzer.analyze_pr(pr_details)
        
        # Assert that the result is correct
        assert result["user_facing"] is True
        assert "docs/api.md" in result["docs_impact"]["update_existing"]
        assert result["pr_number"] == 1
        assert result["pr_title"] == "Update API"
        assert result["pr_url"] == "https://github.com/owner/repo/pull/1"


if __name__ == "__main__":
    unittest.main()
