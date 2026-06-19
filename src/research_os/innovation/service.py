from itertools import combinations
from pathlib import Path

from research_os.models.bundle import PaperBundle
from research_os.models.evidence import EvidenceItem
from research_os.models.innovation import (
    AgentContribution,
    CrossPaperInnovationSet,
    IdeaGraphEdge,
    IdeaGraphNode,
    IdeaAtom,
    InnovationCandidate,
    PaperSection,
    PaperSignal,
    SourceDomain,
)


DOMAIN_KEYWORDS: dict[SourceDomain, tuple[str, ...]] = {
    "ai_ml": (
        "diffusion",
        "transformer",
        "latent",
        "neural",
        "llm",
        "world model",
        "multimodal",
        "attention",
        "embedding",
    ),
    "computer_science": (
        "algorithm",
        "compiler",
        "distributed",
        "cache",
        "scheduling",
        "database",
        "protocol",
        "verification",
        "graph",
        "systems",
    ),
    "mathematics": (
        "theorem",
        "bound",
        "spectral",
        "manifold",
        "topology",
        "algebra",
        "probability",
        "optimization",
        "regularization",
        "geometry",
    ),
    "biology_neuroscience": (
        "hippocamp",
        "synaptic",
        "neuron",
        "cortical",
        "spike",
        "brain",
        "cell",
        "protein",
        "gene",
        "memory consolidation",
        "replay",
    ),
    "physics": (
        "quantum",
        "thermodynamic",
        "statistical mechanics",
        "phase transition",
        "field theory",
        "renormalization",
        "particle",
        "energy landscape",
    ),
    "chemistry": (
        "molecule",
        "molecular",
        "reaction",
        "catalyst",
        "ligand",
        "binding",
        "polymer",
        "synthesis",
    ),
    "medicine_health": (
        "clinical",
        "patient",
        "disease",
        "diagnosis",
        "treatment",
        "medical",
        "imaging",
        "biomarker",
    ),
    "engineering": (
        "control",
        "robotics",
        "sensor",
        "hardware",
        "signal",
        "circuit",
        "feedback",
        "dynamics",
    ),
}

FAMILY_KEYWORDS = (
    ("architecture", ("transformer", "attention", "latent", "memory", "graph", "diffusion")),
    ("algorithm", ("algorithm", "scheduling", "compiler", "protocol", "cache", "distributed")),
    ("theory", ("theorem", "bound", "spectral", "manifold", "geometry", "stability")),
    ("bio_neuro", ("hippocamp", "synaptic", "cortical", "spike", "replay", "neuron")),
    ("optimization", ("optimization", "regularization", "gradient", "loss", "stability")),
    ("data", ("dataset", "augmentation", "sample", "sampling", "data")),
    ("evaluation", ("benchmark", "metric", "evaluation", "protocol")),
)

SECTION_ALIASES = {
    "abstract": "abstract",
    "introduction": "introduction",
    "background": "background",
    "related work": "background",
    "method": "method",
    "methods": "method",
    "methodology": "method",
    "approach": "method",
    "algorithm": "method",
    "experiments": "experiments",
    "experiment": "experiments",
    "evaluation": "experiments",
    "results": "results",
    "discussion": "discussion",
    "limitations": "limitations",
    "limitation": "limitations",
    "conclusion": "conclusion",
}


def build_cross_paper_innovations(
    bundle: PaperBundle,
    top_k: int = 8,
    fulltext_dir: Path | None = None,
) -> CrossPaperInnovationSet:
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")
    paper_items = [item for item in bundle.evidence.items if item.source_type in {"paper", "benchmark"}]
    if not paper_items:
        raise ValueError("Cross-paper innovation extraction requires paper or benchmark evidence.")
    sections = _load_paper_sections(paper_items, fulltext_dir)
    section_ids_by_evidence = _section_ids_by_evidence(sections)
    signals = [_build_signal(item, section_ids_by_evidence.get(item.id, [])) for item in paper_items]
    atoms = _build_atoms(signals, sections)
    agent_contributions = _build_agent_contributions(signals, atoms)
    candidates = _build_candidates(bundle=bundle, atoms=atoms, top_k=top_k)
    agent_contributions.extend(_synthesis_contributions(candidates))
    graph_nodes, graph_edges = _build_idea_graph(signals, sections, atoms, candidates)
    return CrossPaperInnovationSet(
        bundle_id=bundle.id,
        agent_contributions=agent_contributions,
        paper_signals=signals,
        paper_sections=sections,
        idea_atoms=atoms,
        innovation_candidates=candidates,
        idea_graph_nodes=graph_nodes,
        idea_graph_edges=graph_edges,
    )


def _build_signal(item: EvidenceItem, section_ids: list[str] | None = None) -> PaperSignal:
    domain = _classify_domain(item.claim)
    return PaperSignal(
        evidence_id=item.id,
        source_domain=domain,
        source_url=item.url,
        claim=item.claim,
        extracted_terms=_extract_terms(item.claim, domain),
        section_ids=section_ids or [],
        confidence=item.confidence,
    )


def _load_paper_sections(items: list[EvidenceItem], fulltext_dir: Path | None) -> list[PaperSection]:
    if fulltext_dir is None:
        return []
    sections: list[PaperSection] = []
    for item in items:
        source = fulltext_dir / f"{item.id}.txt"
        if not source.exists():
            continue
        text = source.read_text(encoding="utf-8")
        sections.extend(parse_paper_sections(evidence_id=item.id, text=text, confidence=item.confidence))
    return sections


def parse_paper_sections(evidence_id: str, text: str, confidence: float = 0.8) -> list[PaperSection]:
    parsed: list[tuple[str, list[str]]] = []
    current_name = "full_text"
    current_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        heading = _section_heading(line)
        if heading:
            if current_lines:
                parsed.append((current_name, current_lines))
            current_name = heading
            current_lines = []
        elif line:
            current_lines.append(line)
    if current_lines:
        parsed.append((current_name, current_lines))
    if not parsed and text.strip():
        parsed.append(("full_text", [text.strip()]))
    return [
        PaperSection(
            evidence_id=evidence_id,
            section_name=name,
            text=" ".join(lines),
            extracted_terms=_extract_terms(" ".join(lines), _classify_domain(" ".join(lines))),
            confidence=confidence,
        )
        for name, lines in parsed
    ]


def _section_heading(line: str) -> str:
    normalized = line.lower().strip(":0123456789. ")
    if len(normalized) > 40:
        return ""
    return SECTION_ALIASES.get(normalized, "")


def _section_ids_by_evidence(sections: list[PaperSection]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for section in sections:
        grouped.setdefault(section.evidence_id, []).append(section.id)
    return grouped


def _classify_domain(text: str) -> SourceDomain:
    lowered = text.lower()
    scores = {
        domain: sum(1 for token in tokens if token in lowered)
        for domain, tokens in DOMAIN_KEYWORDS.items()
    }
    best_domain, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score == 0:
        return "unknown"
    if sum(1 for score in scores.values() if score == best_score and score > 0) > 1:
        return "interdisciplinary"
    return best_domain


def _extract_terms(text: str, domain: SourceDomain) -> list[str]:
    lowered = text.lower()
    domain_terms = list(DOMAIN_KEYWORDS.get(domain, ()))
    family_terms = [token for _, tokens in FAMILY_KEYWORDS for token in tokens]
    terms = [term for term in domain_terms + family_terms if term in lowered]
    return sorted(set(terms))[:8]


def _build_atoms(signals: list[PaperSignal], sections: list[PaperSection]) -> list[IdeaAtom]:
    sections_by_evidence: dict[str, list[PaperSection]] = {}
    for section in sections:
        sections_by_evidence.setdefault(section.evidence_id, []).append(section)
    atoms: list[IdeaAtom] = []
    for signal in signals:
        evidence_sections = [
            section
            for section in sections_by_evidence.get(signal.evidence_id, [])
            if section.section_name in {"abstract", "method", "experiments", "results", "limitations", "full_text"}
        ]
        if evidence_sections:
            atoms.extend(_build_atom_from_section(signal, section) for section in evidence_sections)
        else:
            atoms.append(_build_atom_from_signal(signal))
    return atoms


def _build_atom_from_signal(signal: PaperSignal) -> IdeaAtom:
    family = _classify_family(signal.claim)
    mechanism = _mechanism_text(signal, family)
    return IdeaAtom(
        evidence_id=signal.evidence_id,
        source_domain=signal.source_domain,
        family=family,
        mechanism=mechanism,
        transfer_hint=_transfer_hint(signal.source_domain, family),
        constraints=_constraints_for_domain(signal.source_domain),
        provenance=[signal.evidence_id],
        confidence=signal.confidence,
    )


def _build_atom_from_section(signal: PaperSignal, section: PaperSection) -> IdeaAtom:
    family = _classify_family(section.text)
    section_domain = _classify_domain(section.text)
    source_domain = section_domain if section_domain != "unknown" else signal.source_domain
    mechanism = _mechanism_text_from_section(section, source_domain, family)
    return IdeaAtom(
        evidence_id=signal.evidence_id,
        section_id=section.id,
        source_domain=source_domain,
        family=family,
        mechanism=mechanism,
        transfer_hint=_transfer_hint(source_domain, family),
        constraints=_constraints_for_domain(source_domain) + _constraints_for_section(section.section_name),
        provenance=[signal.evidence_id, section.id],
        confidence=round((signal.confidence + section.confidence) / 2.0, 4),
    )


def _classify_family(text: str) -> str:
    lowered = text.lower()
    for family, tokens in FAMILY_KEYWORDS:
        if any(token in lowered for token in tokens):
            return family
    return "optimization"


def _mechanism_text(signal: PaperSignal, family: str) -> str:
    terms = ", ".join(signal.extracted_terms[:4]) or "reported mechanism"
    return f"{family} mechanism from {signal.source_domain}: {terms}"


def _mechanism_text_from_section(section: PaperSection, domain: SourceDomain, family: str) -> str:
    terms = ", ".join(section.extracted_terms[:4]) or section.text[:96]
    return f"{family} mechanism from {domain} {section.section_name}: {terms}"


def _transfer_hint(domain: SourceDomain, family: str) -> str:
    if domain == "biology_neuroscience":
        return "Use the biological mechanism as an inductive bias or training schedule, not as benchmark evidence."
    if domain == "mathematics":
        return "Use the formal mechanism as a regularizer, constraint, or analysis tool."
    if domain == "computer_science":
        return "Use the systems or algorithmic mechanism to change execution, search, memory, or scheduling."
    if domain == "ai_ml":
        return "Transfer the model, loss, training, or inference mechanism into the baseline."
    if domain == "physics":
        return "Use the physical principle as a stability prior, dynamics constraint, or energy-based objective."
    if domain == "chemistry":
        return "Use the interaction or binding mechanism as a compositional search or constraint analogy."
    if domain == "medicine_health":
        return "Use the clinical validation pattern as a robustness, subgroup, or failure-analysis protocol."
    if domain == "engineering":
        return "Use the control or feedback mechanism as a runtime adaptation or closed-loop optimization branch."
    return "Treat as a weak cross-domain hint requiring manual validation."


def _constraints_for_domain(domain: SourceDomain) -> list[str]:
    base = ["keep baseline dataset split fixed", "keep metric and evaluation protocol comparable"]
    if domain == "biology_neuroscience":
        return base + ["do not claim biological validity without primary biological evidence"]
    if domain == "mathematics":
        return base + ["do not claim theorem-level guarantees unless assumptions are verified"]
    if domain == "computer_science":
        return base + ["separate algorithmic speedup from model-quality improvement"]
    if domain == "physics":
        return base + ["do not claim physical validity unless the modeled variables match the assumptions"]
    if domain == "chemistry":
        return base + ["do not treat molecular analogy as evidence without task-level validation"]
    if domain == "medicine_health":
        return base + ["do not claim clinical utility without clinical evidence and subgroup checks"]
    if domain == "engineering":
        return base + ["separate controller stability from benchmark metric improvement"]
    return base


def _constraints_for_section(section_name: str) -> list[str]:
    if section_name == "limitations":
        return ["treat limitation-derived ideas as risk controls before treating them as gains"]
    if section_name in {"experiments", "results"}:
        return ["separate reported empirical setup from transferable mechanism"]
    return []


def _build_agent_contributions(
    signals: list[PaperSignal],
    atoms: list[IdeaAtom],
) -> list[AgentContribution]:
    specs: list[tuple[str, str, list[SourceDomain]]] = [
        ("ai-ml-extractor", "ai and machine learning extractor", ["ai_ml", "interdisciplinary"]),
        ("cs-extractor", "computer science systems and theory extractor", ["computer_science", "interdisciplinary"]),
        ("math-extractor", "mathematics extractor", ["mathematics", "interdisciplinary"]),
        ("bio-neuro-extractor", "biology and neuroscience extractor", ["biology_neuroscience", "interdisciplinary"]),
        ("physical-science-extractor", "physics and chemistry extractor", ["physics", "chemistry", "interdisciplinary"]),
        ("engineering-health-extractor", "engineering and medicine extractor", ["engineering", "medicine_health", "interdisciplinary"]),
    ]
    contributions: list[AgentContribution] = []
    for agent_id, role, domains in specs:
        domain_signals = [signal for signal in signals if signal.source_domain in domains]
        domain_atoms = [atom for atom in atoms if atom.source_domain in domains]
        contributions.append(
            AgentContribution(
                agent_id=agent_id,
                role=role,
                source_domains=domains,
                findings=[
                    f"{signal.source_domain}: {', '.join(signal.extracted_terms) or signal.claim[:80]}"
                    for signal in domain_signals
                ],
                atom_ids=[atom.id for atom in domain_atoms],
            )
        )
    return contributions


def _build_candidates(bundle: PaperBundle, atoms: list[IdeaAtom], top_k: int) -> list[InnovationCandidate]:
    ordered_atoms = sorted(atoms, key=lambda atom: atom.confidence, reverse=True)
    cross_domain_pairs = [
        pair
        for pair in combinations(ordered_atoms, 2)
        if pair[0].source_domain != pair[1].source_domain
    ]
    candidates = [_candidate_from_pair(bundle, left, right) for left, right in cross_domain_pairs]
    ranked = sorted(candidates, key=lambda candidate: candidate.score, reverse=True)
    return ranked[:top_k]


def _candidate_from_pair(bundle: PaperBundle, left: IdeaAtom, right: IdeaAtom) -> InnovationCandidate:
    domains = sorted({left.source_domain, right.source_domain})
    families = sorted({left.family, right.family})
    score = round(((left.confidence + right.confidence) / 2.0) + (0.2 if len(domains) > 1 else 0.0), 4)
    title = f"Cross {domains[0]} + {domains[1]} {families[0]} transfer"
    mechanism = f"Combine {left.mechanism} with {right.mechanism} for {bundle.title}."
    return InnovationCandidate(
        title=title,
        source_atom_ids=[left.id, right.id],
        source_domains=domains,
        synthesis_agent="synthesis-agent",
        hypothesis=(
            f"If {left.transfer_hint} and {right.transfer_hint}, the baseline may gain a new "
            "low-to-medium risk branch without changing the benchmark target."
        ),
        mechanism=mechanism,
        why_compatible=(
            "The atoms target different layers of the research stack, so they can be tested as a bounded branch "
            "against the same bundle objective."
        ),
        expected_gain="Potential improvement in stability, sample efficiency, compute efficiency, or transfer quality.",
        risk="Cross-domain analogy may be superficial; validate with ablation and unchanged evaluation settings.",
        required_code_surface=_required_code_surface(families),
        redline_notes=sorted(set(left.constraints + right.constraints)),
        score=score,
    )


def _required_code_surface(families: list[str]) -> list[str]:
    surfaces: list[str] = []
    if "architecture" in families:
        surfaces.extend(["model/", "modules/"])
    if "algorithm" in families:
        surfaces.extend(["runner/", "scheduler/", "search/"])
    if "theory" in families or "optimization" in families:
        surfaces.extend(["losses/", "train.py"])
    if "bio_neuro" in families:
        surfaces.extend(["memory/", "training_schedule.py"])
    if "data" in families:
        surfaces.append("data/")
    if "evaluation" in families:
        surfaces.append("eval/")
    return sorted(set(surfaces or ["experiment_config.yaml"]))


def _synthesis_contributions(candidates: list[InnovationCandidate]) -> list[AgentContribution]:
    return [
        AgentContribution(
            agent_id="synthesis-agent",
            role="cross-domain synthesis agent",
            source_domains=sorted({domain for candidate in candidates for domain in candidate.source_domains}),
            findings=[candidate.title for candidate in candidates],
            atom_ids=[atom_id for candidate in candidates for atom_id in candidate.source_atom_ids],
        ),
        AgentContribution(
            agent_id="redline-agent",
            role="scientific redline agent",
            source_domains=sorted({domain for candidate in candidates for domain in candidate.source_domains}),
            findings=[
                "Every candidate must preserve baseline dataset split, metric, evaluation protocol, and compute budget notes."
            ],
            atom_ids=[],
        ),
    ]


def _build_idea_graph(
    signals: list[PaperSignal],
    sections: list[PaperSection],
    atoms: list[IdeaAtom],
    candidates: list[InnovationCandidate],
) -> tuple[list[IdeaGraphNode], list[IdeaGraphEdge]]:
    signal_domain = {signal.evidence_id: signal.source_domain for signal in signals}
    atom_by_id = {atom.id: atom for atom in atoms}
    nodes: list[IdeaGraphNode] = []
    edges: list[IdeaGraphEdge] = []
    for signal in signals:
        nodes.append(
            IdeaGraphNode(
                id=signal.evidence_id,
                kind="paper_signal",
                label=signal.claim[:96],
                source_domain=signal.source_domain,
            )
        )
    for section in sections:
        nodes.append(
            IdeaGraphNode(
                id=section.id,
                kind="paper_section",
                label=f"{section.evidence_id}:{section.section_name}",
                source_domain=signal_domain.get(section.evidence_id, "unknown"),
            )
        )
        edges.append(
            IdeaGraphEdge(source_id=section.evidence_id, target_id=section.id, relation="has_section")
        )
    for atom in atoms:
        nodes.append(
            IdeaGraphNode(
                id=atom.id,
                kind="idea_atom",
                label=f"{atom.family}:{atom.mechanism[:72]}",
                source_domain=atom.source_domain,
            )
        )
        source_id = atom.section_id or atom.evidence_id
        edges.append(IdeaGraphEdge(source_id=source_id, target_id=atom.id, relation="yields_atom"))
    for candidate in candidates:
        domains = sorted({atom_by_id[atom_id].source_domain for atom_id in candidate.source_atom_ids if atom_id in atom_by_id})
        nodes.append(
            IdeaGraphNode(
                id=candidate.id,
                kind="innovation_candidate",
                label=candidate.title,
                source_domain="+".join(domains) if domains else "unknown",
            )
        )
        for atom_id in candidate.source_atom_ids:
            edges.append(IdeaGraphEdge(source_id=atom_id, target_id=candidate.id, relation="synthesizes"))
    return nodes, edges
