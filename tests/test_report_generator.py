"""
Tests for the report generator module.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.report_generator import ReportGenerator


class TestReportGenerator(unittest.TestCase):
    """
    Test cases for the report generator.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        # Create a temporary directory for test reports
        self.test_dir = tempfile.mkdtemp()
        self.generator = ReportGenerator(self.test_dir)
        
        # Sample PR analysis results
        self.repo_url = "https://github.com/owner/repo"
        self.since_date = datetime(2023, 1, 1)
        self.analysis_results = [
            {
                "pr_number": 1,
                "pr_title": "Add new feature",
                "pr_url": "https://github.com/owner/repo/pull/1",
                "user_facing": True,
                "docs_impact": {
                    "update_existing": ["docs/api.md"],
                    "create_new": ["docs/new-feature.md"],
                    "suggested_content": ["Add section on new authentication flow"]
                },
                "reasoning": "This PR adds a new feature that users will interact with"
            },
            {
                "pr_number": 2,
                "pr_title": "Fix bug",
                "pr_url": "https://github.com/owner/repo/pull/2",
                "user_facing": False,
                "docs_impact": {
                    "update_existing": [],
                    "create_new": [],
                    "suggested_content": []
                },
                "reasoning": "This PR fixes an internal bug with no user-facing changes"
            },
            {
                "pr_number": 3,
                "pr_title": "Update UI",
                "pr_url": "https://github.com/owner/repo/pull/3",
                "user_facing": True,
                "docs_impact": {
                    "update_existing": ["docs/ui.md"],
                    "create_new": [],
                    "suggested_content": ["Update screenshots in UI documentation"]
                },
                "reasoning": "This PR updates the UI that users interact with"
            }
        ]
        
    def tearDown(self):
        """
        Clean up test fixtures.
        """
        # Clean up temporary directory
        for file in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, file))
        os.rmdir(self.test_dir)
        
    def test_generate_report(self):
        """
        Test generating a markdown report.
        """
        # Generate the report
        report_path = self.generator.generate_report(
            self.repo_url,
            self.since_date,
            self.analysis_results
        )
        
        # Assert that the report file exists
        self.assertTrue(os.path.exists(report_path))
        
        # Read the report content
        with open(report_path, "r") as f:
            content = f.read()
            
        # Assert that the report contains expected content
        self.assertIn("# Documentation Update Report for https://github.com/owner/repo", content)
        self.assertIn("Analyzing PRs since: 2023-01-01", content)
        self.assertIn("Total PRs analyzed: 3", content)
        self.assertIn("PRs with user-facing changes: 2", content)
        self.assertIn("### Existing Documentation to Update", content)
        self.assertIn("- docs/api.md", content)
        self.assertIn("- docs/ui.md", content)
        self.assertIn("### New Documentation to Create", content)
        self.assertIn("- docs/new-feature.md", content)
        self.assertIn("### Suggested Content Updates", content)
        self.assertIn("- PR #1: Add section on new authentication flow", content)
        self.assertIn("- PR #3: Update screenshots in UI documentation", content)
        self.assertIn("### PR #1: Add new feature", content)
        self.assertIn("### PR #3: Update UI", content)
        self.assertNotIn("### PR #2: Fix bug", content)  # Non-user-facing PR should not be included
        
    def test_generate_report_no_user_facing(self):
        """
        Test generating a report with no user-facing changes.
        """
        # Create analysis results with no user-facing changes
        analysis_results = [
            {
                "pr_number": 1,
                "pr_title": "Fix bug",
                "pr_url": "https://github.com/owner/repo/pull/1",
                "user_facing": False,
                "docs_impact": {
                    "update_existing": [],
                    "create_new": [],
                    "suggested_content": []
                },
                "reasoning": "This PR fixes an internal bug with no user-facing changes"
            }
        ]
        
        # Generate the report
        report_path = self.generator.generate_report(
            self.repo_url,
            self.since_date,
            analysis_results
        )
        
        # Assert that the report file exists
        self.assertTrue(os.path.exists(report_path))
        
        # Read the report content
        with open(report_path, "r") as f:
            content = f.read()
            
        # Assert that the report contains expected content
        self.assertIn("# Documentation Update Report for https://github.com/owner/repo", content)
        self.assertIn("Total PRs analyzed: 1", content)
        self.assertIn("PRs with user-facing changes: 0", content)
        self.assertIn("No user-facing changes detected in the analyzed PRs.", content)
        self.assertNotIn("### Existing Documentation to Update", content)
        self.assertNotIn("### New Documentation to Create", content)
        self.assertNotIn("### Suggested Content Updates", content)
        
    def test_generate_json_report(self):
        """
        Test generating a JSON report.
        """
        # Generate the report
        report_path = self.generator.generate_json_report(
            self.repo_url,
            self.since_date,
            self.analysis_results
        )
        
        # Assert that the report file exists
        self.assertTrue(os.path.exists(report_path))
        
        # Read the report content
        with open(report_path, "r") as f:
            content = json.load(f)
            
        # Assert that the report contains expected content
        self.assertEqual(content["repository"], self.repo_url)
        self.assertEqual(content["total_prs"], 3)
        self.assertEqual(content["user_facing_prs"], 2)
        self.assertEqual(len(content["analysis_results"]), 3)
        self.assertEqual(content["analysis_results"][0]["pr_number"], 1)
        self.assertEqual(content["analysis_results"][1]["pr_number"], 2)
        self.assertEqual(content["analysis_results"][2]["pr_number"], 3)


if __name__ == "__main__":
    unittest.main()
