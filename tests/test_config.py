"""
Tests for the configuration module.
"""

import os
import unittest
from unittest.mock import patch

from src.config import get_github_config, get_openai_config, validate_config


class TestConfig(unittest.TestCase):
    """
    Test cases for the configuration module.
    """
    
    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test_token",
        "OPENAI_API_KEY": "test_api_key"
    }, clear=True)
    def test_validate_config_valid(self):
        """
        Test validating a valid configuration.
        """
        errors = validate_config()
        self.assertEqual(errors, {})
        
    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "",
        "OPENAI_API_KEY": "test_api_key"
    }, clear=True)
    def test_validate_config_missing_github_token(self):
        """
        Test validating a configuration with a missing GitHub token.
        """
        errors = validate_config()
        self.assertIn("GITHUB_TOKEN", errors)
        
    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test_token",
        "OPENAI_API_KEY": ""
    }, clear=True)
    def test_validate_config_missing_openai_api_key(self):
        """
        Test validating a configuration with a missing OpenAI API key.
        """
        errors = validate_config()
        self.assertIn("OPENAI_API_KEY", errors)
        
    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "",
        "OPENAI_API_KEY": ""
    }, clear=True)
    def test_validate_config_missing_all(self):
        """
        Test validating a configuration with all required values missing.
        """
        errors = validate_config()
        self.assertIn("GITHUB_TOKEN", errors)
        self.assertIn("OPENAI_API_KEY", errors)
        
    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "test_api_key",
        "OPENAI_MODEL": "gpt-4",
        "OPENAI_MAX_TOKENS": "1000",
        "OPENAI_TEMPERATURE": "0.5"
    }, clear=True)
    def test_get_openai_config(self):
        """
        Test getting the OpenAI configuration.
        """
        config = get_openai_config()
        self.assertEqual(config["api_key"], "test_api_key")
        self.assertEqual(config["model"], "gpt-4")
        self.assertEqual(config["max_tokens"], 1000)
        self.assertEqual(config["temperature"], 0.5)
        
    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "test_api_key"
    }, clear=True)
    def test_get_openai_config_defaults(self):
        """
        Test getting the OpenAI configuration with default values.
        """
        config = get_openai_config()
        self.assertEqual(config["api_key"], "test_api_key")
        self.assertEqual(config["model"], "gpt-4-turbo")
        self.assertEqual(config["max_tokens"], 2000)
        self.assertEqual(config["temperature"], 0.7)
        
    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test_token",
        "GITHUB_API_URL": "https://github.example.com/api/v3"
    }, clear=True)
    def test_get_github_config(self):
        """
        Test getting the GitHub configuration.
        """
        config = get_github_config()
        self.assertEqual(config["token"], "test_token")
        self.assertEqual(config["api_url"], "https://github.example.com/api/v3")
        
    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test_token"
    }, clear=True)
    def test_get_github_config_defaults(self):
        """
        Test getting the GitHub configuration with default values.
        """
        config = get_github_config()
        self.assertEqual(config["token"], "test_token")
        self.assertEqual(config["api_url"], "https://api.github.com")


if __name__ == "__main__":
    unittest.main()
