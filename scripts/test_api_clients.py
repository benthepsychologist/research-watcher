#!/usr/bin/env python3
"""
Test script for external API clients.

Tests that OpenAlex, Semantic Scholar, and arXiv clients
can fetch and normalize papers.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.openalex import OpenAlexClient
from app.services.semantic_scholar import SemanticScholarClient
from app.services.arxiv_client import ArxivClient

def test_openalex():
    """Test OpenAlex client"""
    print("\n" + "="*60)
    print("TESTING OPENALEX CLIENT")
    print("="*60)

    client = OpenAlexClient()
    papers = client.search_papers("machine learning", days_back=30, max_results=5)

    print(f"✓ Fetched {len(papers)} papers from OpenAlex")

    if papers:
        paper = papers[0]
        print(f"\nSample paper:")
        print(f"  Title: {paper.get('title', 'N/A')}")
        print(f"  Authors: {', '.join(paper.get('authors', [])[:3])}")
        print(f"  Year: {paper.get('year', 'N/A')}")
        print(f"  Citations: {paper.get('citations', 0)}")
        print(f"  Score: {paper.get('score', 'Not scored yet')}")
        print(f"  Provenance: {paper.get('provenance', {})}")

        # Check required fields
        assert 'title' in paper, "Missing title"
        assert 'authors' in paper, "Missing authors"
        assert 'provenance' in paper, "Missing provenance"
        assert paper['provenance']['openalex'] == True, "Wrong provenance flag"

        print("✓ All required fields present")
    else:
        print("⚠ No papers found (may be rate limited or query issue)")

    return len(papers) > 0

def test_semantic_scholar():
    """Test Semantic Scholar client"""
    print("\n" + "="*60)
    print("TESTING SEMANTIC SCHOLAR CLIENT")
    print("="*60)

    client = SemanticScholarClient()
    papers = client.search_papers("neural networks", days_back=30, max_results=5)

    print(f"✓ Fetched {len(papers)} papers from Semantic Scholar")

    if papers:
        paper = papers[0]
        print(f"\nSample paper:")
        print(f"  Title: {paper.get('title', 'N/A')}")
        print(f"  Authors: {', '.join(paper.get('authors', [])[:3])}")
        print(f"  Year: {paper.get('year', 'N/A')}")
        print(f"  Citations: {paper.get('citations', 0)}")
        print(f"  Provenance: {paper.get('provenance', {})}")

        assert 'title' in paper, "Missing title"
        assert 'provenance' in paper, "Missing provenance"
        assert paper['provenance']['s2'] == True, "Wrong provenance flag"

        print("✓ All required fields present")
    else:
        print("⚠ No papers found (may be rate limited)")

    return len(papers) > 0

def test_arxiv():
    """Test arXiv client"""
    print("\n" + "="*60)
    print("TESTING ARXIV CLIENT")
    print("="*60)

    client = ArxivClient()
    papers = client.search_papers("quantum computing", days_back=30, max_results=5)

    print(f"✓ Fetched {len(papers)} papers from arXiv")

    if papers:
        paper = papers[0]
        print(f"\nSample paper:")
        print(f"  Title: {paper.get('title', 'N/A')}")
        print(f"  Authors: {', '.join(paper.get('authors', [])[:3])}")
        print(f"  Year: {paper.get('year', 'N/A')}")
        print(f"  arXiv ID: {paper.get('arxivId', 'N/A')}")
        print(f"  Open Access: {paper.get('oa', False)}")
        print(f"  Provenance: {paper.get('provenance', {})}")

        assert 'title' in paper, "Missing title"
        assert 'arxivId' in paper, "Missing arXiv ID"
        assert paper.get('oa') == True, "arXiv papers should be OA"
        assert paper['provenance']['arxiv'] == True, "Wrong provenance flag"

        print("✓ All required fields present")
    else:
        print("⚠ No papers found")

    return len(papers) > 0

def test_deduplication():
    """Test deduplication logic"""
    print("\n" + "="*60)
    print("TESTING DEDUPLICATION")
    print("="*60)

    from app.services.collector import deduplicate_papers, generate_paper_id

    # Create test papers with same DOI
    paper1 = {
        'title': 'Test Paper',
        'doi': '10.1234/test',
        'citations': 10,
        'provenance': {'openalex': True, 's2': False}
    }

    paper2 = {
        'title': 'Test Paper',
        'doi': '10.1234/TEST',  # Different case
        'citations': 15,  # Higher citations
        'abstract': 'This is a test',
        'provenance': {'openalex': False, 's2': True}
    }

    papers = [paper1, paper2]
    deduplicated = deduplicate_papers(papers)

    print(f"Input: {len(papers)} papers")
    print(f"Output: {len(deduplicated)} papers")

    assert len(deduplicated) == 1, "Should deduplicate to 1 paper"

    result = deduplicated[0]
    print(f"\nMerged paper:")
    print(f"  Citations: {result.get('citations')} (should be max: 15)")
    print(f"  Has abstract: {bool(result.get('abstract'))}")
    print(f"  Provenance: {result.get('provenance')}")

    assert result['citations'] == 15, "Should use higher citation count"
    assert result.get('abstract'), "Should merge abstract"
    assert result['provenance']['openalex'] == True, "Should merge provenance"
    assert result['provenance']['s2'] == True, "Should merge provenance"

    print("✓ Deduplication working correctly")
    return True

def test_scoring():
    """Test scoring algorithm"""
    print("\n" + "="*60)
    print("TESTING SCORING ALGORITHM")
    print("="*60)

    from app.services.collector import score_paper

    # Recent, high-citation, OA paper
    paper1 = {
        'title': 'Test',
        'year': 2025,
        'citations': 100,
        'oa': True,
        'abstract': 'Test abstract',
        'venue': 'Nature'
    }

    # Old, low-citation paper
    paper2 = {
        'title': 'Test',
        'year': 2010,
        'citations': 1,
        'oa': False,
        'venue': 'Unknown'
    }

    score1 = score_paper(paper1)
    score2 = score_paper(paper2)

    print(f"\nHigh-quality paper score: {score1:.2f}/100")
    print(f"Low-quality paper score: {score2:.2f}/100")

    assert score1 > score2, "High-quality paper should score higher"
    assert score1 > 50, "High-quality paper should score > 50"

    print("✓ Scoring algorithm working correctly")
    return True

if __name__ == "__main__":
    print("\n🧪 TESTING RESEARCH WATCHER API CLIENTS")
    print("="*60)

    results = {}

    try:
        results['openalex'] = test_openalex()
    except Exception as e:
        print(f"❌ OpenAlex test failed: {e}")
        results['openalex'] = False

    try:
        results['s2'] = test_semantic_scholar()
    except Exception as e:
        print(f"❌ Semantic Scholar test failed: {e}")
        results['s2'] = False

    try:
        results['arxiv'] = test_arxiv()
    except Exception as e:
        print(f"❌ arXiv test failed: {e}")
        results['arxiv'] = False

    try:
        results['dedup'] = test_deduplication()
    except Exception as e:
        print(f"❌ Deduplication test failed: {e}")
        results['dedup'] = False

    try:
        results['scoring'] = test_scoring()
    except Exception as e:
        print(f"❌ Scoring test failed: {e}")
        results['scoring'] = False

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for test, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{test:20s} {status}")

    all_passed = all(results.values())
    print("\n" + ("="*60))

    if all_passed:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
