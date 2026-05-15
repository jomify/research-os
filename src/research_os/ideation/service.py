from research_os.models.branch import BranchCandidate, BranchResult, BranchSet
from research_os.models.bundle import PaperBundle
from research_os.models.idea import IDEA_FAMILIES, Idea, IdeaFamily
from research_os.models.ranking import BranchRanking, RankedBranchItem


_IDEA_TEMPLATES: dict[IdeaFamily, tuple[str, str, str, float, int]] = {
    "hyperparameter": (
        "Tune optimizer and schedule",
        "Low-risk sweeps can establish whether the reproduced baseline is under-tuned.",
        "Run a constrained sweep over learning rate, warmup, batch size, and weight decay.",
        2.0,
        2,
    ),
    "training_strategy": (
        "Change training curriculum",
        "Training order and loss scheduling often moves metrics without changing model shape.",
        "Add staged training, auxiliary loss weighting, or progressive resolution.",
        4.0,
        4,
    ),
    "architecture": (
        "Modify model component",
        "Architecture branches test whether the paper bottleneck is representational.",
        "Swap or augment the main block, attention path, or latent bottleneck.",
        8.0,
        7,
    ),
    "data": (
        "Improve data mixture",
        "Dataset balance and filtering can dominate benchmark movement.",
        "Adjust sampling, filtering, augmentation, or benchmark-specific data coverage.",
        5.0,
        5,
    ),
    "inference": (
        "Tune inference path",
        "Inference-only changes are fast to evaluate after a baseline exists.",
        "Search decoding, ensembling, test-time augmentation, or solver settings.",
        1.5,
        2,
    ),
    "paper_transfer": (
        "Transfer a recent paper idea",
        "Nearby papers may contain reusable improvements not present in the bundle.",
        "Port one compatible method from related literature into this baseline.",
        6.0,
        6,
    ),
}


def generate_ideas(bundle: PaperBundle) -> list[Idea]:
    return [
        Idea(
            family=family,
            title=template[0],
            rationale=f"{template[1]} Bundle: {bundle.title}",
            proposed_change=template[2],
        )
        for family in IDEA_FAMILIES
        for template in (_IDEA_TEMPLATES[family],)
    ]


def build_branch_set(bundle: PaperBundle) -> BranchSet:
    candidates = []
    for idea in generate_ideas(bundle):
        template = _IDEA_TEMPLATES[idea.family]
        candidates.append(
            BranchCandidate(
                parent_bundle_id=bundle.id,
                family=idea.family,
                title=idea.title,
                rationale=idea.rationale,
                proposed_change=idea.proposed_change,
                resource_cost_estimate=template[3],
                complexity=template[4],
            )
        )
    return BranchSet(parent_bundle_id=bundle.id, candidates=candidates)


def simulate_results_from_candidates(candidates: list[BranchCandidate]) -> list[BranchResult]:
    """Generate plausible estimated results from branch candidates for ranking preview."""
    import random
    random.seed(42)
    simulated: list[BranchResult] = []
    for c in candidates:
        base = {"hyperparameter": 0.8, "training_strategy": 1.5, "architecture": 2.5,
                "data": 1.8, "inference": 0.6, "paper_transfer": 2.0}
        improvement = base.get(c.family, 1.0) + random.uniform(-0.3, 0.5)
        simulated.append(BranchResult(
            candidate_id=c.id,
            family=c.family,
            metric_improvement=round(max(0.1, improvement), 4),
            resource_cost=c.resource_cost_estimate,
            complexity=c.complexity,
        ))
    return simulated


def rank_branch_results(parent_bundle_id: str, results: list[BranchResult]) -> BranchRanking:
    ranked = sorted(results, key=_branch_score, reverse=True)
    return BranchRanking(
        parent_bundle_id=parent_bundle_id,
        items=[
            RankedBranchItem(
                rank=index,
                candidate_id=result.candidate_id,
                family=result.family,
                score=round(_branch_score(result), 6),
                metric_improvement=result.metric_improvement,
                resource_cost=result.resource_cost,
                complexity=result.complexity,
            )
            for index, result in enumerate(ranked, start=1)
        ],
    )


def _branch_score(result: BranchResult) -> float:
    return (result.metric_improvement * 100.0) - (result.resource_cost * 0.1) - (result.complexity * 0.05)
