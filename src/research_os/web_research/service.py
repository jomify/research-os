from research_os.models.brief import ResearchBrief
from research_os.models.evidence import EvidenceItem, EvidenceLedger
from research_os.web_research.arxiv import search_arxiv
from research_os.web_research.github import search_github_repositories
from research_os.web_research.huggingface import search_huggingface_datasets


def _query_url(source_type: str, brief: ResearchBrief) -> str:
    query = "+".join(brief.prompt.strip().split())
    return f"query://{source_type}/{query}"


def build_stub_evidence(brief: ResearchBrief) -> EvidenceLedger:
    items = []
    for source_type, claim_prefix in (
        ("paper", "Find primary paper sources for"),
        ("code", "Find official code repositories for"),
        ("dataset", "Find official dataset or benchmark data pages for"),
        ("benchmark", "Find metric and benchmark protocol sources for"),
    ):
        items.append(
            EvidenceItem(
                source_type=source_type,
                url=_query_url(source_type, brief),
                claim=f"{claim_prefix}: {brief.prompt}",
                confidence=0.9,
            )
        )
    return EvidenceLedger(items=items)


def _replace_source_items(ledger: EvidenceLedger, source_type: str, items: list[EvidenceItem]) -> None:
    if items:
        ledger.items = [item for item in ledger.items if item.source_type != source_type]
        ledger.items.extend(items)


def _append_error(ledger: EvidenceLedger, source_type: str, provider: str, exc: OSError) -> None:
    ledger.items.append(
        EvidenceItem(
            source_type=source_type,
            url=f"error://{provider}",
            claim=f"{provider} search failed: {exc}",
            confidence=0.0,
        )
    )


def build_live_evidence(
    brief: ResearchBrief,
    max_papers: int = 5,
    max_repos: int = 5,
    max_datasets: int = 5,
) -> EvidenceLedger:
    ledger = build_stub_evidence(brief)
    try:
        _replace_source_items(ledger, "paper", search_arxiv(brief, max_results=max_papers))
    except OSError as exc:
        _append_error(ledger, "paper", "arxiv", exc)
    try:
        _replace_source_items(ledger, "code", search_github_repositories(brief, max_results=max_repos))
    except OSError as exc:
        _append_error(ledger, "code", "github", exc)
    try:
        _replace_source_items(ledger, "dataset", search_huggingface_datasets(brief, max_results=max_datasets))
    except OSError as exc:
        _append_error(ledger, "dataset", "huggingface", exc)
    return ledger
