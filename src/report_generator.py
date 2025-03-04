"""
Report generator module for DocuPR.

This module generates markdown reports based on PR analysis.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Generator for documentation reports based on PR analysis.
    """
    
    def __init__(self, output_dir: str = "."):
        """
        Initialize the report generator.
        
        Args:
            output_dir (str): Directory to save reports to
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_report(
        self, 
        repo_url: str, 
        since_date: datetime, 
        analysis_results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a markdown report based on PR analysis.
        
        Args:
            repo_url (str): GitHub repository URL
            since_date (datetime): Date to filter PRs by
            analysis_results (List[Dict[str, Any]]): List of PR analysis results
            
        Returns:
            str: Path to the generated report
        """
        # Filter for user-facing changes
        user_facing_prs = [pr for pr in analysis_results if pr.get("user_facing", False)]
        
        # Generate the report filename
        repo_name = repo_url.strip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"docupr_{repo_name}_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        # Generate the report content
        with open(filepath, "w") as f:
            # Report header
            f.write(f"# Documentation Update Report for {repo_url}\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Analyzing PRs since: {since_date.strftime('%Y-%m-%d')}\n\n")
            
            # Summary section
            f.write("## Summary\n\n")
            f.write(f"Total PRs analyzed: {len(analysis_results)}\n")
            f.write(f"PRs with user-facing changes: {len(user_facing_prs)}\n\n")
            
            if not user_facing_prs:
                f.write("No user-facing changes detected in the analyzed PRs.\n\n")
                return filepath
                
            # Documentation updates needed section
            f.write("## Documentation Updates Needed\n\n")
            
            # Collect all documentation updates
            all_updates = {
                "update_existing": set(),
                "create_new": set(),
                "suggested_content": []
            }
            
            for pr in user_facing_prs:
                docs_impact = pr.get("docs_impact", {})
                
                for update in docs_impact.get("update_existing", []):
                    all_updates["update_existing"].add(update)
                    
                for new_doc in docs_impact.get("create_new", []):
                    all_updates["create_new"].add(new_doc)
                    
                for suggestion in docs_impact.get("suggested_content", []):
                    all_updates["suggested_content"].append({
                        "pr": pr.get("pr_number"),
                        "content": suggestion
                    })
            
            # Existing docs to update
            if all_updates["update_existing"]:
                f.write("### Existing Documentation to Update\n\n")
                for doc in sorted(all_updates["update_existing"]):
                    f.write(f"- {doc}\n")
                f.write("\n")
                
            # New docs to create
            if all_updates["create_new"]:
                f.write("### New Documentation to Create\n\n")
                for doc in sorted(all_updates["create_new"]):
                    f.write(f"- {doc}\n")
                f.write("\n")
                
            # Suggested content
            if all_updates["suggested_content"]:
                f.write("### Suggested Content Updates\n\n")
                for suggestion in all_updates["suggested_content"]:
                    f.write(f"- PR #{suggestion['pr']}: {suggestion['content']}\n")
                f.write("\n")
                
            # Detailed PR analysis
            f.write("## Detailed PR Analysis\n\n")
            
            for pr in user_facing_prs:
                f.write(f"### PR #{pr.get('pr_number')}: {pr.get('pr_title')}\n\n")
                f.write(f"- URL: {pr.get('pr_url')}\n")
                f.write(f"- User-facing: Yes\n")
                
                if "reasoning" in pr:
                    f.write(f"- Reasoning: {pr.get('reasoning')}\n\n")
                    
                docs_impact = pr.get("docs_impact", {})
                
                if docs_impact.get("update_existing"):
                    f.write("#### Existing Documentation to Update\n\n")
                    for doc in docs_impact.get("update_existing", []):
                        f.write(f"- {doc}\n")
                    f.write("\n")
                    
                if docs_impact.get("create_new"):
                    f.write("#### New Documentation to Create\n\n")
                    for doc in docs_impact.get("create_new", []):
                        f.write(f"- {doc}\n")
                    f.write("\n")
                    
                if docs_impact.get("suggested_content"):
                    f.write("#### Suggested Content\n\n")
                    for suggestion in docs_impact.get("suggested_content", []):
                        f.write(f"- {suggestion}\n")
                    f.write("\n")
                    
        logger.info(f"Report generated: {filepath}")
        return filepath
        
    def generate_json_report(
        self, 
        repo_url: str, 
        since_date: datetime, 
        analysis_results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a JSON report based on PR analysis.
        
        Args:
            repo_url (str): GitHub repository URL
            since_date (datetime): Date to filter PRs by
            analysis_results (List[Dict[str, Any]]): List of PR analysis results
            
        Returns:
            str: Path to the generated report
        """
        # Generate the report filename
        repo_name = repo_url.strip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"docupr_{repo_name}_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        # Generate the report content
        report = {
            "repository": repo_url,
            "generated_at": datetime.now().isoformat(),
            "since_date": since_date.isoformat(),
            "total_prs": len(analysis_results),
            "user_facing_prs": len([pr for pr in analysis_results if pr.get("user_facing", False)]),
            "analysis_results": analysis_results
        }
        
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"JSON report generated: {filepath}")
        return filepath
