import json
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from research_os.models.brief import ResearchBrief
from research_os.models.evidence import EvidenceItem
from research_os.web_research.keywords import extract_keywords


def build_huggingface_dataset_search_url(brief: ResearchBrief, max_results: int = 5) -> str:
    keywords = extract_keywords(brief.prompt, brief.domain_hints)
    # HuggingFace search works best with 1-2 terms; use domain hints + top keyword
    domain_terms = [dh for dh in brief.domain_hints if dh in keywords or True]
    search_terms = (domain_terms + keywords)[:2]
    query = quote_plus(" ".join(search_terms))
    return f"https://huggingface.co/api/datasets?search={query}&limit={max_results}&full=false"


def parse_huggingface_datasets(payload: str) -> list[EvidenceItem]:
    data = json.loads(payload)
    items: list[EvidenceItem] = []
    for dataset in data:
        dataset_id = dataset.get("id")
        if not dataset_id:
            continue
        downloads = dataset.get("downloads", 0)
        likes = dataset.get("likes", 0)
        tags = ", ".join(dataset.get("tags", [])[:5])
        claim = f"Hugging Face dataset: {dataset_id} (downloads={downloads}, likes={likes})"
        if tags:
            claim = f"{claim} - tags: {tags}"
        items.append(
            EvidenceItem(
                source_type="dataset",
                url=f"https://huggingface.co/datasets/{dataset_id}",
                claim=claim,
                confidence=0.9,
            )
        )
    return items


def search_huggingface_datasets(
    brief: ResearchBrief,
    max_results: int = 5,
    timeout: float = 20.0,
) -> list[EvidenceItem]:
    request = Request(
        build_huggingface_dataset_search_url(brief, max_results=max_results),
        headers={"User-Agent": "research-os"},
    )
    with urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8", errors="replace")
    return parse_huggingface_datasets(payload)
