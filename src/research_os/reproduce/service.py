from research_os.models.bundle import PaperBundle
from research_os.models.repro import ReproPlan
from research_os.runner import get_runner


def build_repro_plan(bundle: PaperBundle, runner: str) -> ReproPlan:
    get_runner(runner)
    return ReproPlan.from_bundle(bundle=bundle, runner=runner)
