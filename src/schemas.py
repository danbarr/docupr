"""
Schema definitions for DocuPR.

This module contains Pydantic models for data validation.
"""

from typing import List
from pydantic import BaseModel


class DocsImpact(BaseModel):
    """Model for documentation impact data."""
    update_existing: List[str] = []
    create_new: List[str] = []
    suggested_content: List[str] = []


class AnalysisResult(BaseModel):
    """Model for OpenAI analysis result."""
    user_facing: bool
    docs_impact: DocsImpact
    reasoning: str
