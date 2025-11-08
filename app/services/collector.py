"""
Paper collection, deduplication, and scoring logic.

Orchestrates fetching papers from multiple sources, deduplicating,
and scoring them for user digests.
"""

import hashlib
from typing import List, Dict, Set, Tuple
from datetime import datetime

from .openalex import OpenAlexClient
from .semantic_scholar import SemanticScholarClient
from .arxiv_client import ArxivClient


def normalize_doi(doi: str) -> str:
    """Normalize DOI for deduplication"""
    if not doi:
        return ""
    return doi.lower().strip().replace('https://doi.org/', '').replace('http://dx.doi.org/', '')


def normalize_arxiv_id(arxiv_id: str) -> str:
    """Normalize arXiv ID for deduplication"""
    if not arxiv_id:
        return ""
    # Remove version number (e.g., "2301.12345v2" -> "2301.12345")
    return arxiv_id.split('v')[0].strip()


def generate_paper_id(paper: Dict) -> str:
    """
    Generate stable paper ID for deduplication.

    Priority: DOI > arXiv ID > title hash

    Args:
        paper: Normalized paper dict

    Returns:
        Stable paper ID
    """
    # Try DOI first
    doi = paper.get('doi')
    if doi:
        norm_doi = normalize_doi(doi)
        if norm_doi:
            return f'doi:{norm_doi}'

    # Try arXiv ID
    arxiv_id = paper.get('arxivId')
    if arxiv_id:
        norm_arxiv = normalize_arxiv_id(arxiv_id)
        if norm_arxiv:
            return f'arxiv:{norm_arxiv}'

    # Fall back to title hash
    title = paper.get('title', '').lower().strip()
    if title:
        title_hash = hashlib.md5(title.encode()).hexdigest()[:16]
        return f'title:{title_hash}'

    # Last resort: use source ID if available
    source_id = paper.get('id', '')
    if source_id:
        return f'source:{source_id}'

    # Should never happen, but return empty string
    return ''


def deduplicate_papers(papers: List[Dict]) -> List[Dict]:
    """
    Deduplicate papers and merge metadata from multiple sources.

    Args:
        papers: List of papers from various sources

    Returns:
        Deduplicated list with merged metadata
    """
    paper_map: Dict[str, Dict] = {}

    for paper in papers:
        paper_id = generate_paper_id(paper)
        if not paper_id:
            continue

        if paper_id in paper_map:
            # Merge with existing paper
            existing = paper_map[paper_id]

            # Merge provenance flags
            for source in ['openalex', 's2', 'crossref', 'arxiv']:
                if paper.get('provenance', {}).get(source):
                    existing['provenance'][source] = True

            # Prefer higher citation counts
            if paper.get('citations', 0) > existing.get('citations', 0):
                existing['citations'] = paper['citations']

            # Fill in missing fields
            for field in ['abstract', 'doi', 'arxivId', 'venue']:
                if not existing.get(field) and paper.get(field):
                    existing[field] = paper[field]

            # Update OA status if found
            if paper.get('oa') and not existing.get('oa'):
                existing['oa'] = paper['oa']
                if paper.get('links', {}).get('oa'):
                    existing['links']['oa'] = paper['links']['oa']

        else:
            # Add paper ID and store
            paper['paperId'] = paper_id
            paper_map[paper_id] = paper

    return list(paper_map.values())


def score_paper(paper: Dict) -> float:
    """
    Score paper for ranking in digest.

    Factors:
    - Citation count (weighted)
    - Venue prestige (heuristic)
    - Recency (more recent = higher)
    - Open access availability

    Args:
        paper: Paper dict

    Returns:
        Score (0-100)
    """
    score = 0.0

    # Citation count (up to 30 points, log scale)
    citations = paper.get('citations', 0)
    if citations > 0:
        import math
        # log10(1) = 0, log10(10) = 1, log10(100) = 2, log10(1000) = 3
        # Cap at 1000 citations for normalization
        citation_score = min(30.0, math.log10(citations + 1) * 10)
        score += citation_score

    # Recency (up to 25 points)
    year = paper.get('year')
    if year:
        current_year = datetime.utcnow().year
        years_old = current_year - year
        # Recent papers score higher
        if years_old == 0:
            score += 25.0  # This year
        elif years_old == 1:
            score += 20.0  # Last year
        elif years_old <= 2:
            score += 15.0
        elif years_old <= 5:
            score += 10.0
        else:
            score += max(0, 10 - years_old)  # Decay

    # Venue prestige (up to 20 points, very basic heuristic)
    venue = paper.get('venue', '').lower()
    if venue:
        # Top-tier venues (simplified list)
        tier1 = ['nature', 'science', 'cell', 'nejm', 'lancet', 'jama']
        tier2 = ['pnas', 'nature communications', 'plos', 'acm', 'ieee']

        if any(t in venue for t in tier1):
            score += 20.0
        elif any(t in venue for t in tier2):
            score += 15.0
        elif 'arxiv' not in venue:  # Peer-reviewed but not top-tier
            score += 10.0

    # Open access (up to 15 points)
    if paper.get('oa'):
        score += 15.0

    # Has abstract (up to 10 points - indicates completeness)
    if paper.get('abstract'):
        score += 10.0

    return min(100.0, score)


def collect_and_rank(seeds: List[str], days_back: int = 7, max_per_seed: int = 20) -> List[Dict]:
    """
    Collect papers from all sources, deduplicate, and rank by score.

    Args:
        seeds: List of search queries (keywords, authors, etc.)
        days_back: How many days back to search
        max_per_seed: Max results per seed per source

    Returns:
        Ranked list of deduplicated papers
    """
    # Initialize clients
    openalex = OpenAlexClient()
    s2 = SemanticScholarClient()
    arxiv = ArxivClient()

    all_papers = []

    # Fetch from each source for each seed
    for seed in seeds:
        # OpenAlex
        try:
            papers = openalex.search_papers(seed, days_back, max_per_seed)
            all_papers.extend(papers)
        except Exception as e:
            print(f'OpenAlex error for seed "{seed}": {str(e)}')

        # Semantic Scholar
        try:
            papers = s2.search_papers(seed, days_back, max_per_seed)
            all_papers.extend(papers)
        except Exception as e:
            print(f'Semantic Scholar error for seed "{seed}": {str(e)}')

        # arXiv
        try:
            papers = arxiv.search_papers(seed, days_back, max_per_seed)
            all_papers.extend(papers)
        except Exception as e:
            print(f'arXiv error for seed "{seed}": {str(e)}')

    # Deduplicate
    unique_papers = deduplicate_papers(all_papers)

    # Score each paper
    for paper in unique_papers:
        paper['score'] = score_paper(paper)

    # Sort by score descending
    unique_papers.sort(key=lambda p: p['score'], reverse=True)

    # Add timestamp
    timestamp = datetime.utcnow().isoformat() + 'Z'
    for paper in unique_papers:
        paper['updatedAt'] = timestamp

    return unique_papers
