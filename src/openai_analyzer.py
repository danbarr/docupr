"""
OpenAI analyzer module for DocuPR.

This module handles the analysis of pull requests using OpenAI's API.
"""

import json
import logging
import sys
import time
from typing import Dict, List, Any, Optional

from openai import OpenAI
from pydantic import ValidationError

from .config import get_openai_config
from .schemas import AnalysisResult, DocsImpact

logger = logging.getLogger(__name__)

class OpenAIAnalyzer:
    """
    Analyzer for pull requests using OpenAI's API.
    """
    
    def __init__(self):
        """
        Initialize the OpenAI analyzer.
        """
        config = get_openai_config()
        
        # Initialize the OpenAI client with the API key
        # Create a custom http client with no proxy to avoid the 'proxies' error
        import httpx
        http_client = httpx.Client()
        
        # Initialize the OpenAI client with explicit parameters to avoid proxy issues
        self.client = OpenAI(
            api_key=config["api_key"],
            http_client=http_client,
            base_url=config["base_url"],
            timeout=60.0
        )
        
        self.model = config["model"]
        self.max_tokens = config["max_tokens"]
        self.temperature = config["temperature"]
        self.extra_instructions = config["extra_instructions"]
        
        # Rate limiting
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_per_minute = 20  # Adjust based on your OpenAI rate limits
        
    async def _rate_limit(self) -> None:
        """
        Implement rate limiting for OpenAI API calls.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        # If we've made requests in the last minute, check if we need to wait
        if time_since_last_request < 60 and self.request_count >= self.rate_limit_per_minute:
            wait_time = 60 - time_since_last_request
            logger.info(f"Rate limiting: waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
            self.request_count = 0
            
        # If it's been more than a minute since the last request, reset the counter
        elif time_since_last_request >= 60:
            self.request_count = 0
            
        self.request_count += 1
        self.last_request_time = time.time()
        
    async def _get_openai_response(self, system_prompt: str, user_message: str) -> str:
        """
        Get a response from the OpenAI API.
        
        Args:
            system_prompt (str): The system prompt to send to OpenAI
            user_message (str): The user message to send to OpenAI
            
        Returns:
            str: The response content from OpenAI
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    
    def _extract_json_from_markdown(self, content: str) -> Optional[str]:
        """
        Extract JSON from markdown code blocks.
        
        Args:
            content (str): The content to extract JSON from
            
        Returns:
            Optional[str]: The extracted JSON string, or None if not found
        """
        # Check for markdown code blocks
        if "```json" in content and "```" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if start > 6 and end > start:
                return content[start:end].strip()
        
        # Check for any JSON-like structure
        start_idx = content.find("{")
        end_idx = content.rfind("}")
        
        if start_idx >= 0 and end_idx > start_idx:
            return content[start_idx:end_idx + 1]
            
        return None
    
    def _create_default_result(self) -> Dict[str, Any]:
        """
        Create a default result when parsing fails.
        
        Returns:
            Dict[str, Any]: The default result
        """
        return {
            "user_facing": True,  # Assume user-facing by default
            "docs_impact": {
                "update_existing": [],
                "create_new": [],
                "suggested_content": []
            },
            "reasoning": "Extracted from non-JSON response"
        }
    
    def _parse_openai_response(self, content: str) -> Dict[str, Any]:
        """
        Parse the OpenAI response content into a structured result.
        
        Args:
            content (str): The response content from OpenAI
            
        Returns:
            Dict[str, Any]: The parsed result
        """
        # Clean and prepare the content for JSON parsing
        content = content.strip()
        
        # Try direct parsing with validation
        try:
            data = json.loads(content)
            return AnalysisResult(**data).model_dump()
        except (json.JSONDecodeError, ValidationError):
            # Only log warning on JSON decode error
            if isinstance(sys.exc_info()[1], json.JSONDecodeError):
                logger.warning("Failed to parse OpenAI response as JSON, attempting extraction")
        
        # Try extracting JSON from markdown
        json_str = self._extract_json_from_markdown(content)
        if json_str:
            try:
                data = json.loads(json_str)
                return AnalysisResult(**data).model_dump()
            except (json.JSONDecodeError, ValidationError):
                pass
        
        # If all extraction attempts fail, create a default result
        logger.error(f"Failed to extract valid JSON from OpenAI response")
        
        # Create default result
        result = self._create_default_result()
        
        # Try to extract useful information from the raw response
        if "documentation" in content.lower():
            # Extract sentences containing "documentation"
            sentences = content.split(". ")
            for sentence in sentences:
                if "documentation" in sentence.lower():
                    result["docs_impact"]["suggested_content"].append(sentence.strip())
        
        return result
    
    async def analyze_pr(self, pr_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a pull request to determine if it contains user-facing changes
        and what documentation updates are needed.
        
        Args:
            pr_details (Dict[str, Any]): Pull request details
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        await self._rate_limit()
        
        # Prepare the prompt for OpenAI
        system_prompt = """
        You are a documentation specialist analyzing GitHub pull requests. Your task is to:

        1. Determine if this PR contains end-user facing changes (Yes/No)
           - End-user facing changes are those that affect the people who use the finished software product, 
             NOT the developers working on the code
           
           Examples of end-user facing changes:
           - Changes to CLI commands or arguments
           - Changes to configuration file formats
           - Changes to APIs that users directly interact with
           - New features or modifications to existing features that users interact with
           - Changes to error messages shown to users
           - Changes to user documentation
           
           Examples of NON-user facing changes:
           - Internal refactoring
           - Code cleanup or formatting
           - Development documentation updates
           - Test improvements
           - CI/CD pipeline changes
           - Internal logging changes
           - Performance optimizations (unless they require user action)
           - Security fixes (unless they require user action)
           
        2. Identify documentation impact:
           - Only suggest documentation updates for changes that affect end-users
           - Existing user documentation files that need updates
           - New user documentation sections that should be created
           - Suggested content for user-facing documentation updates

        Analyze the PR title, description, and code changes (diff) to make your determination.
        Be conservative - if a change is purely internal, mark it as not user-facing.
        
        Your response MUST be a valid JSON object matching this structure:
        {
          "user_facing": boolean,
          "docs_impact": {
            "update_existing": ["list of existing docs to update"],
            "create_new": ["list of new docs to create"],
            "suggested_content": ["list of suggested content or sections"]
          },
          "reasoning": "brief explanation of your analysis and why it is/isn't user-facing"
        }
        
        Do not include any text outside the JSON object.
        """
        
        # Add any extra instructions if provided
        if self.extra_instructions:
            system_prompt += f"\n\nAdditional instructions:\n{self.extra_instructions}"
        
        # Prepare the user message with PR details
        user_message = f"""
        Pull Request #{pr_details['number']}: {pr_details['title']}
        
        Description:
        {pr_details['body']}
        
        Changed Files:
        {json.dumps(pr_details['changed_files'], indent=2)}
        
        Diff:
        ```diff
        {pr_details['diff'][:10000]}  # Limit diff size to avoid token limits
        ```
        
        Please analyze this PR and determine if it contains user-facing changes and what documentation updates are needed.
        """
        
        try:
            # Get response from OpenAI
            content = await self._get_openai_response(system_prompt, user_message)
            
            # Parse the response
            result = self._parse_openai_response(content)
            
            # Add PR metadata to the result
            result["pr_number"] = pr_details["number"]
            result["pr_title"] = pr_details["title"]
            result["pr_url"] = pr_details["url"]
            
            return result
                
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {
                "pr_number": pr_details["number"],
                "pr_title": pr_details["title"],
                "pr_url": pr_details["url"],
                "user_facing": False,
                "docs_impact": {
                    "update_existing": [],
                    "create_new": [],
                    "suggested_content": []
                },
                "reasoning": f"Error: {str(e)}",
                "error": str(e)
            }
