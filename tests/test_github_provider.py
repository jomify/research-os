import json

from research_os.models.brief import ResearchBrief
from research_os.web_research.github import build_github_search_url, parse_github_repositories


def test_build_github_search_url_targets_public_repositories() -> None:
    brief = ResearchBrief.from_prompt("diffusion world model github repo")
    url = build_github_search_url(brief, max_results=4)
    assert "api.github.com/search/repositories" in url
    assert "diffusion" in url
    assert "world" in url
    assert "model" in url
    assert "sort=stars" in url
    assert "per_page=4" in url


def test_parse_github_repositories_returns_code_evidence() -> None:
    payload = json.dumps(
        {
            "items": [
                {
                    "full_name": "research/example-world-model",
                    "html_url": "https://github.com/research/example-world-model",
                    "description": "Diffusion world model baseline",
                    "stargazers_count": 128,
                }
            ]
        }
    )
    items = parse_github_repositories(payload)
    assert len(items) == 1
    assert items[0].source_type == "code"
    assert items[0].url == "https://github.com/research/example-world-model"
    assert "research/example-world-model" in items[0].claim
    assert "stars=128" in items[0].claim
