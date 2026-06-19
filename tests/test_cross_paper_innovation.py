import json
from pathlib import Path

from typer.testing import CliRunner

from research_os import cli
from research_os.cli import app
from research_os.models.bundle import PaperBundle
from research_os.models.evidence import EvidenceItem, EvidenceLedger
from research_os.innovation.service import build_cross_paper_innovations, parse_paper_sections


def _broad_bundle() -> PaperBundle:
    return PaperBundle(
        id="bundle-cross",
        brief_id="brief-cross",
        title="World model research synthesis",
        summary="Find cross-disciplinary innovation candidates for a world model baseline",
        domain_hints=["world_model"],
        evidence=EvidenceLedger(
            items=[
                EvidenceItem(
                    id="paper-ai",
                    source_type="paper",
                    url="https://arxiv.org/abs/ai",
                    claim="arXiv paper: Diffusion world models with transformer latent memory improve rollout prediction.",
                    confidence=0.95,
                ),
                EvidenceItem(
                    id="paper-cs",
                    source_type="paper",
                    url="https://dl.acm.org/alg",
                    claim="Systems paper: Graph scheduling algorithm reduces cache misses in distributed execution.",
                    confidence=0.9,
                ),
                EvidenceItem(
                    id="paper-math",
                    source_type="paper",
                    url="https://math.example/theorem",
                    claim="Mathematics paper: Spectral manifold regularization gives stability bounds for optimization.",
                    confidence=0.88,
                ),
                EvidenceItem(
                    id="paper-neuro",
                    source_type="paper",
                    url="https://neuro.example/hippocampus",
                    claim="Neuroscience paper: Hippocampal replay and synaptic gating support efficient memory consolidation.",
                    confidence=0.86,
                ),
            ]
        ),
    )


def test_cross_paper_innovation_extracts_broad_domain_agents_and_candidates() -> None:
    result = build_cross_paper_innovations(_broad_bundle(), top_k=6)

    assert result.bundle_id == "bundle-cross"
    domains = {signal.source_domain for signal in result.paper_signals}
    assert {"ai_ml", "computer_science", "mathematics", "biology_neuroscience"} <= domains
    agent_roles = {agent.role for agent in result.agent_contributions}
    assert {
        "ai and machine learning extractor",
        "computer science systems and theory extractor",
        "mathematics extractor",
        "biology and neuroscience extractor",
        "cross-domain synthesis agent",
        "scientific redline agent",
    } <= agent_roles
    assert result.idea_atoms
    assert result.innovation_candidates
    assert any(len(candidate.source_domains) >= 2 for candidate in result.innovation_candidates)
    assert all(candidate.redline_notes for candidate in result.innovation_candidates)


def test_cross_paper_innovation_cli_writes_json(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    workspace = cli.WorkspacePaths(tmp_path)
    workspace.ensure()
    bundle_path = workspace.bundle_dir / "bundle-cross.json"
    bundle_path.write_text(json.dumps(_broad_bundle().model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")

    result = CliRunner().invoke(app, ["cross-ideas", "bundle-cross", "--top-k", "4"])

    assert result.exit_code == 0
    output_path = Path(result.stdout.strip())
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert output_path.parent == tmp_path / "workspace" / "cross_ideas"
    assert payload["bundle_id"] == "bundle-cross"
    assert len(payload["innovation_candidates"]) <= 4
    assert {agent["agent_id"] for agent in payload["agent_contributions"]} >= {
        "ai-ml-extractor",
        "cs-extractor",
        "math-extractor",
        "bio-neuro-extractor",
        "synthesis-agent",
        "redline-agent",
    }


def test_cross_paper_innovation_rejects_empty_bundle() -> None:
    bundle = PaperBundle(
        id="empty",
        brief_id="brief",
        title="empty",
        summary="empty",
        evidence=EvidenceLedger(items=[]),
    )

    try:
        build_cross_paper_innovations(bundle)
    except ValueError as exc:
        assert "evidence" in str(exc).lower()
    else:
        raise AssertionError("empty evidence bundle should fail")


def test_cross_paper_innovation_supports_extensible_non_ai_domains() -> None:
    bundle = PaperBundle(
        id="broad",
        brief_id="brief",
        title="Broad synthesis",
        summary="Use non-AI papers to create hypotheses",
        evidence=EvidenceLedger(
            items=[
                EvidenceItem(
                    source_type="paper",
                    url="https://physics.example/q",
                    claim="Physics paper: Quantum phase transition suggests an energy landscape prior.",
                ),
                EvidenceItem(
                    source_type="paper",
                    url="https://chem.example/r",
                    claim="Chemistry paper: Molecular catalyst binding improves reaction pathway search.",
                ),
                EvidenceItem(
                    source_type="paper",
                    url="https://eng.example/c",
                    claim="Engineering paper: Feedback control stabilizes robotics sensor dynamics.",
                ),
            ]
        ),
    )

    result = build_cross_paper_innovations(bundle, top_k=3)

    domains = {signal.source_domain for signal in result.paper_signals}
    assert {"physics", "chemistry", "engineering"} <= domains
    assert any(agent.agent_id == "physical-science-extractor" for agent in result.agent_contributions)
    assert any(agent.agent_id == "engineering-health-extractor" for agent in result.agent_contributions)
    assert result.innovation_candidates


def test_cross_paper_innovation_rejects_invalid_top_k() -> None:
    try:
        build_cross_paper_innovations(_broad_bundle(), top_k=0)
    except ValueError as exc:
        assert "top_k" in str(exc)
    else:
        raise AssertionError("top_k=0 should fail")


def test_parse_paper_sections_recovers_methods_and_limitations() -> None:
    sections = parse_paper_sections(
        evidence_id="paper-ai",
        text="""
        Abstract
        Diffusion world model abstract.
        Methods
        We add transformer latent memory and spectral regularization.
        Experiments
        The benchmark metric is held fixed.
        Limitations
        Long horizon rollout remains unstable.
        """,
    )

    by_name = {section.section_name: section for section in sections}
    assert {"abstract", "method", "experiments", "limitations"} <= set(by_name)
    assert "transformer" in by_name["method"].extracted_terms
    assert "benchmark" in by_name["experiments"].extracted_terms


def test_cross_paper_innovation_uses_fulltext_sections_and_idea_graph(tmp_path) -> None:
    bundle = _broad_bundle()
    fulltext_dir = tmp_path / "fulltext"
    fulltext_dir.mkdir()
    (fulltext_dir / "paper-ai.txt").write_text(
        """
        Abstract
        Diffusion world models need stable latent rollout.
        Methods
        Transformer latent memory is trained with spectral regularization.
        Limitations
        Rollout stability degrades under long horizon evaluation.
        """,
        encoding="utf-8",
    )

    result = build_cross_paper_innovations(bundle, top_k=4, fulltext_dir=fulltext_dir)

    assert result.paper_sections
    assert any(atom.section_id for atom in result.idea_atoms)
    assert result.idea_graph_nodes
    assert result.idea_graph_edges
    relations = {edge.relation for edge in result.idea_graph_edges}
    assert {"has_section", "yields_atom", "synthesizes"} <= relations


def test_cross_paper_innovation_cli_accepts_fulltext_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    workspace = cli.WorkspacePaths(tmp_path)
    workspace.ensure()
    bundle_path = workspace.bundle_dir / "bundle-cross.json"
    bundle_path.write_text(json.dumps(_broad_bundle().model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    fulltext_dir = tmp_path / "fulltext"
    fulltext_dir.mkdir()
    (fulltext_dir / "paper-ai.txt").write_text(
        "Methods\nTransformer latent memory with spectral regularization.\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        ["cross-ideas", "bundle-cross", "--top-k", "3", "--fulltext-dir", str(fulltext_dir)],
    )

    assert result.exit_code == 0
    payload = json.loads(Path(result.stdout.strip()).read_text(encoding="utf-8"))
    assert payload["paper_sections"]
    assert payload["idea_graph_nodes"]
    assert payload["idea_graph_edges"]
