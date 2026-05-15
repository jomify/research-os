from pathlib import Path


class WorkspacePaths:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.workspace_dir = root / "workspace"
        self.intake_dir = self.workspace_dir / "intake"
        self.bundle_dir = self.workspace_dir / "bundles"
        self.evidence_dir = self.workspace_dir / "evidence"
        self.repro_plan_dir = self.workspace_dir / "repro_plans"

    def ensure(self) -> None:
        for path in (self.intake_dir, self.bundle_dir, self.evidence_dir, self.repro_plan_dir):
            path.mkdir(parents=True, exist_ok=True)
