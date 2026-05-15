import json

from research_os.models.brief import ResearchBrief
from research_os.web_research.huggingface import (
    build_huggingface_dataset_search_url,
    parse_huggingface_datasets,
)


def test_build_huggingface_dataset_search_url_targets_datasets() -> None:
    brief = ResearchBrief.from_prompt("world model driving dataset")
    url = build_huggingface_dataset_search_url(brief, max_results=2)
    assert "huggingface.co/api/datasets" in url
    assert "search=world+model" in url
    assert "limit=2" in url


def test_parse_huggingface_datasets_returns_dataset_evidence() -> None:
    payload = json.dumps(
        [
            {
                "id": "org/world-model-dataset",
                "downloads": 42,
                "likes": 7,
                "tags": ["video", "world-model"],
            }
        ]
    )
    items = parse_huggingface_datasets(payload)
    assert len(items) == 1
    assert items[0].source_type == "dataset"
    assert items[0].url == "https://huggingface.co/datasets/org/world-model-dataset"
    assert "org/world-model-dataset" in items[0].claim
    assert "downloads=42" in items[0].claim
