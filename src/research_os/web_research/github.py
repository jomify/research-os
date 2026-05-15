import json
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from research_os.models.brief import ResearchBrief
from research_os.models.evidence import EvidenceItem
from research_os.web_research.keywords import extract_keywords


def build_github_search_url(brief: ResearchBrief, max_results: int = 5) -> str:
    keywords = extract_keywords(brief.prompt, brief.domain_hints)
    query = quote_plus("+".join(keywords[:6]))
    return (
        "https://api.github.com/search/repositories"
        f"?q={query}"
        "&sort=stars"
        "&order=desc"
        f"&per_page={max_results}"
    )


def parse_github_repositories(payload: str) -> list[EvidenceItem]:
    data = json.loads(payload)
    items: list[EvidenceItem] = []
    for repo in data.get("items", []):
        full_name = repo.get("full_name")
        url = repo.get("html_url")
        if not full_name or not url:
            continue
        description = repo.get("description") or "no description"
        stars = repo.get("stargazers_count", 0)
        claim = f"GitHub repo: {full_name} (stars={stars}) - {description}"
        items.append(EvidenceItem(source_type="code", url=url, claim=claim, confidence=0.9))
    return items


def search_github_repositories(
    brief: ResearchBrief,
    max_results: int = 5,
    timeout: float = 20.0,
) -> list[EvidenceItem]:
    request = Request(
        build_github_search_url(brief, max_results=max_results),
        headers={"Accept": "application/vnd.github+json", "User-Agent": "research-os"},
    )
    with urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8", errors="replace")
    return parse_github_repositories(payload)
