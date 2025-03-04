"""
Configuration module for DocuPR.

This module loads environment variables and provides configuration settings
for the GitHub and OpenAI API clients.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# User-facing change patterns (file patterns that typically indicate user-facing changes)
USER_FACING_PATTERNS = [
    "docs/**/*",
    "*.md",
    "src/ui/**/*",
    "src/public/**/*",
    "*.html",
    "*.css",
    "*.js",
    "config/*",
]

def validate_config() -> Dict[str, Any]:
    """
    Validate that all required configuration variables are set.
    
    Returns:
        Dict[str, Any]: Dictionary of configuration errors, if any
    """
    errors = {}
    
    github_token = os.getenv("GITHUB_TOKEN")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not github_token:
        errors["GITHUB_TOKEN"] = "GitHub Personal Access Token is required"
    
    if not openai_api_key:
        errors["OPENAI_API_KEY"] = "OpenAI API Key is required"
    
    return errors

def get_openai_config() -> Dict[str, Any]:
    """
    Get OpenAI API configuration.
    
    Returns:
        Dict[str, Any]: OpenAI configuration dictionary
    """
    return {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": os.getenv("OPENAI_MODEL", "gpt-4-turbo"),
        "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "2000")),
        "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
    }

def get_github_config() -> Dict[str, Any]:
    """
    Get GitHub API configuration.
    
    Returns:
        Dict[str, Any]: GitHub configuration dictionary
    """
    return {
        "token": os.getenv("GITHUB_TOKEN"),
        "api_url": os.getenv("GITHUB_API_URL", "https://api.github.com"),
    }
