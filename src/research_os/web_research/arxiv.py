from urllib.parse import quote_plus
from urllib.request import urlopen
from xml.etree import ElementTree

from research_os.models.brief import ResearchBrief
from research_os.models.evidence import EvidenceItem
from research_os.web_research.keywords import extract_keywords


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def build_arxiv_search_url(brief: ResearchBrief, max_results: int = 5) -> str:
    keywords = extract_keywords(brief.prompt, brief.domain_hints)
    # Domain hints + top keywords with AND for precision
    domain_terms = [dh.replace("-", " ").replace("_", " ") for dh in brief.domain_hints]
    key_terms = [kw for kw in keywords if kw not in domain_terms][:4]
    all_terms = domain_terms + key_terms
    clauses = [f'all:"{term}"' if " " in term else f"all:{term}" for term in all_terms[:6]]
    query = quote_plus(" AND ".join(clauses))
    return (
        "https://export.arxiv.org/api/query"
        f"?search_query={query}"
        "&sortBy=relevance"
        "&sortOrder=descending"
        f"&max_results={max_results}"
    )


def parse_arxiv_atom(payload: str) -> list[EvidenceItem]:
    root = ElementTree.fromstring(payload)
    items: list[EvidenceItem] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
        summary = (entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").strip()
        url = (entry.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
        if not title or not url:
            continue
        claim = f"arXiv paper: {title}"
        if summary:
            claim = f"{claim} - {summary[:240]}"
        items.append(EvidenceItem(source_type="paper", url=url, claim=claim, confidence=0.95))
    return items


def search_arxiv(brief: ResearchBrief, max_results: int = 5, timeout: float = 20.0) -> list[EvidenceItem]:
    url = build_arxiv_search_url(brief, max_results=max_results)
    with urlopen(url, timeout=timeout) as response:
        payload = response.read().decode("utf-8", errors="replace")
    return parse_arxiv_atom(payload)
