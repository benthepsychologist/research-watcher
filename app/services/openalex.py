"""
OpenAlex API client.

Fetches academic papers from OpenAlex API based on search queries.
Docs: https://docs.openalex.org/
"""

import os
import requests
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class OpenAlexClient:
    """Client for OpenAlex API"""

    BASE_URL = "https://api.openalex.org"

    def __init__(self, email: Optional[str] = None):
        """
        Initialize OpenAlex client.

        Args:
            email: Contact email for polite pool (faster rate limits)
        """
        self.email = email or os.getenv('OPENALEX_EMAIL', 'noreply@example.com')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'ResearchWatcher/1.0 (mailto:{self.email})'
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
            query: Search query (keywords, author names, etc.)
            days_back: How many days back to search
            max_results: Maximum number of results to return

        Returns:
            List of paper dictionaries with normalized fields
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        # Build filter query
        # Search in title and abstract, filter by publication date
        filters = [
            f'from_publication_date:{start_date.strftime("%Y-%m-%d")}',
            f'to_publication_date:{end_date.strftime("%Y-%m-%d")}'
        ]

        params = {
            'search': query,
            'filter': ','.join(filters),
            'per_page': min(max_results, 100),  # API max is 100
            'page': 1,
            'sort': 'publication_date:desc'
        }

        try:
            response = self.session.get(
                f'{self.BASE_URL}/works',
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            papers = []
            for work in data.get('results', []):
                paper = self._normalize_paper(work)
                if paper:
                    papers.append(paper)

            return papers[:max_results]

        except requests.RequestException as e:
            print(f'OpenAlex API error: {str(e)}')
            return []

    def _normalize_paper(self, work: Dict) -> Optional[Dict]:
        """
        Normalize OpenAlex work to our paper schema.

        Args:
            work: Raw OpenAlex work object

        Returns:
            Normalized paper dict or None if invalid
        """
        try:
            # Extract DOI
            doi = work.get('doi', '').replace('https://doi.org/', '') if work.get('doi') else None

            # Extract authors
            authors = []
            for authorship in work.get('authorships', [])[:10]:  # Limit to first 10
                if authorship and isinstance(authorship, dict):
                    author = authorship.get('author', {}) or {}
                    name = author.get('display_name')
                    if name:
                        authors.append(name)

            # Extract venue
            venue = None
            primary_location = work.get('primary_location', {})
            if primary_location:
                source = primary_location.get('source', {})
                venue = source.get('display_name')

            # Extract publication date
            pub_date = work.get('publication_date')

            # Citation count
            cited_by_count = work.get('cited_by_count', 0)

            # Open access status
            open_access = work.get('open_access', {})
            is_oa = open_access.get('is_oa', False)
            oa_url = open_access.get('oa_url')

            # Abstract (inverted index - need to reconstruct)
            abstract = self._reconstruct_abstract(work.get('abstract_inverted_index'))

            return {
                'id': work.get('id', '').replace('https://openalex.org/', ''),
                'title': work.get('title'),
                'authors': authors,
                'venue': venue,
                'year': int(work.get('publication_year')) if work.get('publication_year') else None,
                'date': pub_date,
                'doi': doi,
                'abstract': abstract,
                'citations': cited_by_count,
                'oa': is_oa,
                'links': {
                    'doi': f'https://doi.org/{doi}' if doi else None,
                    'oa': oa_url
                },
                'provenance': {
                    'openalex': True,
                    's2': False,
                    'crossref': False,
                    'arxiv': False
                }
            }

        except Exception as e:
            print(f'Error normalizing OpenAlex paper: {str(e)}')
            return None

    def _reconstruct_abstract(self, inverted_index: Optional[Dict]) -> Optional[str]:
        """
        Reconstruct abstract from OpenAlex inverted index.

        Args:
            inverted_index: Dict mapping words to position lists

        Returns:
            Reconstructed abstract text or None
        """
        if not inverted_index:
            return None

        try:
            # Create list of (position, word) tuples
            words_with_positions = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    words_with_positions.append((pos, word))

            # Sort by position and join
            words_with_positions.sort(key=lambda x: x[0])
            return ' '.join(word for _, word in words_with_positions)

        except Exception:
            return None
