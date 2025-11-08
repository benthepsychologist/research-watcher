"""
arXiv API client.

Fetches preprints from arXiv.org API.
Docs: https://info.arxiv.org/help/api/index.html
"""

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class ArxivClient:
    """Client for arXiv API"""

    BASE_URL = "http://export.arxiv.org/api/query"

    def search_papers(
        self,
        query: str,
        days_back: int = 7,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Search arXiv for papers matching query.

        Args:
            query: Search query
            days_back: How many days back to search (unused - arXiv sorts by relevance)
            max_results: Maximum results

        Returns:
            List of normalized paper dicts
        """
        params = {
            'search_query': f'all:{query}',
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }

        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom',
                  'arxiv': 'http://arxiv.org/schemas/atom'}

            papers = []
            for entry in root.findall('atom:entry', ns):
                paper = self._parse_entry(entry, ns)
                if paper:
                    papers.append(paper)

            return papers

        except Exception as e:
            print(f'arXiv API error: {str(e)}')
            return []

    def _parse_entry(self, entry, ns) -> Optional[Dict]:
        """Parse arXiv entry XML to normalized paper dict"""
        try:
            # Extract arXiv ID from URL
            id_url = entry.find('atom:id', ns).text
            arxiv_id = id_url.split('/abs/')[-1]

            # Title
            title = entry.find('atom:title', ns).text.strip()

            # Authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name = author.find('atom:name', ns).text
                authors.append(name)

            # Abstract
            abstract = entry.find('atom:summary', ns).text.strip()

            # Published date
            published = entry.find('atom:published', ns).text
            pub_date = published.split('T')[0]  # Extract YYYY-MM-DD

            # PDF link
            pdf_link = None
            for link in entry.findall('atom:link', ns):
                if link.get('title') == 'pdf':
                    pdf_link = link.get('href')
                    break

            # Primary category
            primary_cat = entry.find('arxiv:primary_category', ns)
            category = primary_cat.get('term') if primary_cat is not None else None

            return {
                'id': arxiv_id,
                'title': title,
                'authors': authors[:10],  # Limit to 10
                'venue': f'arXiv:{category}' if category else 'arXiv',
                'year': int(pub_date[:4]),
                'date': pub_date,
                'arxivId': arxiv_id,
                'abstract': abstract,
                'citations': 0,  # arXiv doesn't provide citation counts
                'oa': True,  # All arXiv papers are open access
                'links': {
                    'arxiv': f'https://arxiv.org/abs/{arxiv_id}',
                    'oa': pdf_link
                },
                'provenance': {
                    'openalex': False,
                    's2': False,
                    'crossref': False,
                    'arxiv': True
                }
            }

        except Exception as e:
            print(f'Error parsing arXiv entry: {str(e)}')
            return None
