"""
Command-line interface for DocuPR.

This module provides the CLI for the DocuPR tool.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import click

from .config import validate_config
from .github_client import GitHubClient
from .openai_analyzer import OpenAIAnalyzer
from .report_generator import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def analyze_repository(
    repo_url: str,
    since_date: Optional[datetime] = None,
    release_tag: Optional[str] = None,
    token: Optional[str] = None,
    output_dir: str = ".",
    json_output: bool = False
) -> str:
    """
    Analyze a GitHub repository and generate a documentation update report.
    
    Args:
        repo_url (str): GitHub repository URL
        since_date (Optional[datetime]): Date to filter PRs by
        token (Optional[str]): GitHub OAuth token
        output_dir (str): Directory to save reports to
        json_output (bool): Whether to generate a JSON report
        
    Returns:
        str: Path to the generated report
    """
    # Validate configuration
    config_errors = validate_config()
    if config_errors:
        for key, error in config_errors.items():
            logger.error(f"Configuration error: {error}")
        raise ValueError("Invalid configuration. Please check your .env file.")
    
    # Initialize clients
    github_client = GitHubClient(token)
    openai_analyzer = OpenAIAnalyzer()
    report_generator = ReportGenerator(output_dir)
    
    # Authenticate with GitHub
    if not token:
        token = await github_client.authenticate()
    
    # Get repository
    logger.info(f"Fetching repository: {repo_url}")
    repo = github_client.get_repository(repo_url)
    
    # Get release date if not provided
    if not since_date:
        if release_tag:
            logger.info(f"Fetching release date for tag: {release_tag}")
        else:
            logger.info("Fetching latest release date")
            
        since_date = await github_client.get_release_date(repo, release_tag)
        
        if not since_date:
            # Default to 30 days ago if no releases found
            since_date = datetime.now() - timedelta(days=30)
            logger.info(f"No releases found, using date from 30 days ago: {since_date}")
        else:
            if release_tag:
                logger.info(f"Using release date for tag {release_tag}: {since_date}")
            else:
                logger.info(f"Using latest release date: {since_date}")
    
    # Get PRs since the date
    logger.info(f"Fetching PRs since {since_date}")
    prs = await github_client.get_prs_since_date(repo, since_date)
    logger.info(f"Found {len(prs)} PRs")
    
    if not prs:
        logger.warning("No PRs found since the specified date")
        return report_generator.generate_report(repo_url, since_date, [])
    
    # Analyze PRs
    logger.info("Analyzing PRs")
    analysis_results = []
    
    for i, pr in enumerate(prs):
        logger.info(f"Analyzing PR #{pr.number} ({i+1}/{len(prs)})")
        pr_details = await github_client.get_pr_details(pr)
        analysis = await openai_analyzer.analyze_pr(pr_details)
        analysis_results.append(analysis)
    
    # Generate report
    logger.info("Generating report")
    if json_output:
        return report_generator.generate_json_report(repo_url, since_date, analysis_results)
    else:
        return report_generator.generate_report(repo_url, since_date, analysis_results)

@click.group()
def cli():
    """DocuPR - Analyze PRs and generate documentation update reports."""
    pass

@cli.command()
@click.argument("repo_url")
@click.option(
    "--since", 
    help="Date to filter PRs by (YYYY-MM-DD). Defaults to latest release date or 30 days ago."
)
@click.option(
    "--release-tag", 
    help="Release tag to start from. Defaults to latest release."
)
@click.option(
    "--token", 
    help="GitHub Personal Access Token. If not provided, will use the token from the .env file."
)
@click.option(
    "--output-dir", 
    default=".", 
    help="Directory to save reports to. Defaults to current directory."
)
@click.option(
    "--json", 
    is_flag=True, 
    help="Generate a JSON report instead of markdown."
)
def analyze(
    repo_url: str, 
    since: Optional[str] = None,
    release_tag: Optional[str] = None,
    token: Optional[str] = None,
    output_dir: str = ".",
    json: bool = False
):
    """
    Analyze a GitHub repository and generate a documentation update report.
    
    REPO_URL is the URL of the GitHub repository to analyze.
    """
    # Parse since date if provided
    since_date = None
    if since:
        try:
            since_date = datetime.strptime(since, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid date format: {since}. Expected YYYY-MM-DD.")
            sys.exit(1)
    
    # Run the analysis
    try:
        report_path = asyncio.run(
            analyze_repository(
                repo_url=repo_url,
                since_date=since_date,
                release_tag=release_tag,
                token=token,
                output_dir=output_dir,
                json_output=json
            )
        )
        
        logger.info(f"Report generated: {report_path}")
        logger.info(f"To view the report: cat {report_path}")
        
    except Exception as e:
        logger.error(f"Error analyzing repository: {e}")
        sys.exit(1)

if __name__ == "__main__":
    cli()
