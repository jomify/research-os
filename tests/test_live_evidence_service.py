from research_os.models.brief import ResearchBrief
from research_os.models.evidence import EvidenceItem
from research_os.web_research import service


def test_live_evidence_replaces_paper_code_and_dataset_placeholders(monkeypatch) -> None:
    brief = ResearchBrief.from_prompt("diffusion world model repo dataset")

    monkeypatch.setattr(
        service,
        "search_arxiv",
        lambda brief, max_results: [EvidenceItem(source_type="paper", url="https://arxiv.org/abs/x", claim="paper")],
    )
    monkeypatch.setattr(
        service,
        "search_github_repositories",
        lambda brief, max_results: [EvidenceItem(source_type="code", url="https://github.com/a/b", claim="repo")],
    )
    monkeypatch.setattr(
        service,
        "search_huggingface_datasets",
        lambda brief, max_results: [
            EvidenceItem(source_type="dataset", url="https://huggingface.co/datasets/a/b", claim="dataset")
        ],
    )

    ledger = service.build_live_evidence(brief)
    by_type = {item.source_type: item for item in ledger.items}
    assert by_type["paper"].url == "https://arxiv.org/abs/x"
    assert by_type["code"].url == "https://github.com/a/b"
    assert by_type["dataset"].url == "https://huggingface.co/datasets/a/b"
    assert by_type["benchmark"].url.startswith("query://benchmark/")
