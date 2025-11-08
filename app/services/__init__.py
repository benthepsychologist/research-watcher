"""
External API services for fetching academic papers.
"""

from .openalex import OpenAlexClient
from .semantic_scholar import SemanticScholarClient
from .arxiv_client import ArxivClient

__all__ = ["OpenAlexClient", "SemanticScholarClient", "ArxivClient"]

