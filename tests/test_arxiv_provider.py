from research_os.models.brief import ResearchBrief
from research_os.web_research.arxiv import build_arxiv_search_url, parse_arxiv_atom


ARXIV_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2501.00001v1</id>
    <title>World Models With Diffusion Backbones</title>
    <summary>We study a world model benchmark.</summary>
  </entry>
</feed>
"""


def test_build_arxiv_search_url_uses_prompt_query() -> None:
    brief = ResearchBrief.from_prompt("diffusion world model")
    url = build_arxiv_search_url(brief, max_results=3)
    assert "export.arxiv.org/api/query" in url
    assert "all%3Adiffusion" in url
    assert "all%3Aworld" in url
    assert "max_results=3" in url


def test_parse_arxiv_atom_returns_paper_evidence() -> None:
    items = parse_arxiv_atom(ARXIV_SAMPLE)
    assert len(items) == 1
    assert items[0].source_type == "paper"
    assert items[0].url == "http://arxiv.org/abs/2501.00001v1"
    assert "World Models With Diffusion Backbones" in items[0].claim
