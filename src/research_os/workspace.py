from pathlib import Path


class WorkspacePaths:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.workspace_dir = root / "workspace"
        self.intake_dir = self.workspace_dir / "intake"
        self.bundle_dir = self.workspace_dir / "bundles"
        self.evidence_dir = self.workspace_dir / "evidence"
        self.repro_plan_dir = self.workspace_dir / "repro_plans"
        self.cluster_plan_dir = self.workspace_dir / "cluster_plans"
        self.cluster_session_dir = self.workspace_dir / "cluster_sessions"
        self.cluster_dispatch_dir = self.workspace_dir / "cluster_dispatches"
        self.cross_idea_dir = self.workspace_dir / "cross_ideas"
        self.idea_review_dir = self.workspace_dir / "idea_reviews"

    def ensure(self) -> None:
        for path in (
            self.intake_dir,
            self.bundle_dir,
            self.evidence_dir,
            self.repro_plan_dir,
            self.cluster_plan_dir,
            self.cluster_session_dir,
            self.cluster_dispatch_dir,
            self.cross_idea_dir,
            self.idea_review_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)
