"""
Semantic Scholar API client.

Fetches academic papers from Semantic Scholar API.
Docs: https://api.semanticscholar.org/api-docs/
"""

import os
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class SemanticScholarClient:
    """Client for Semantic Scholar API"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Semantic Scholar client.

        Args:
            api_key: Optional API key for higher rate limits
        """
        self.api_key = api_key or os.getenv('S2_API_KEY')
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                'x-api-key': self.api_key
            })

    def search_papers(
        self,
        query: str,
        days_back: int = 7,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Search for papers matching query from recent days.

        Args:
            query: Search query
            days_back: How many days back to search
            max_results: Maximum number of results

        Returns:
            List of normalized paper dicts
        """
        # Calculate year filter (S2 doesn't support date range, only year)
        current_year = datetime.utcnow().year
        year_filter = f'{current_year}-'

        params = {
            'query': query,
            'year': year_filter,
            'limit': min(max_results, 100),  # API max is 100
            'fields': 'paperId,title,authors,venue,year,publicationDate,abstract,citationCount,isOpenAccess,openAccessPdf,externalIds'
        }

        try:
            response = self.session.get(
                f'{self.BASE_URL}/paper/search',
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            papers = []
            for paper in data.get('data', []):
                normalized = self._normalize_paper(paper)
                if normalized:
                    papers.append(normalized)

            return papers[:max_results]

        except requests.RequestException as e:
            print(f'Semantic Scholar API error: {str(e)}')
            return []

    def _normalize_paper(self, paper: Dict) -> Optional[Dict]:
        """
        Normalize S2 paper to our schema.

        Args:
            paper: Raw S2 paper object

        Returns:
            Normalized paper dict or None
        """
        try:
            # Extract external IDs
            external_ids = paper.get('externalIds', {}) or {}
            doi = external_ids.get('DOI')
            arxiv_id = external_ids.get('ArXiv')

            # Extract authors
            authors = []
            for author in (paper.get('authors', []) or [])[:10]:
                name = author.get('name')
                if name:
                    authors.append(name)

            # Open access
            is_oa = paper.get('isOpenAccess', False)
            oa_pdf = paper.get('openAccessPdf', {})
            oa_url = oa_pdf.get('url') if oa_pdf else None

            return {
                'id': paper.get('paperId'),
                'title': paper.get('title'),
                'authors': authors,
                'venue': paper.get('venue'),
                'year': paper.get('year'),
                'date': paper.get('publicationDate'),
                'doi': doi,
                'arxivId': arxiv_id,
                'abstract': paper.get('abstract'),
                'citations': paper.get('citationCount', 0),
                'oa': is_oa,
                'links': {
                    'doi': f'https://doi.org/{doi}' if doi else None,
                    'arxiv': f'https://arxiv.org/abs/{arxiv_id}' if arxiv_id else None,
                    'oa': oa_url
                },
                'provenance': {
                    'openalex': False,
                    's2': True,
                    'crossref': False,
                    'arxiv': False
                }
            }

        except Exception as e:
            print(f'Error normalizing S2 paper: {str(e)}')
            return None
