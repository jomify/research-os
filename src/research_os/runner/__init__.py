from research_os.runner.base import Runner
from research_os.runner.local import RUNNER as LOCAL_RUNNER
from research_os.runner.slurm import RUNNER as SLURM_RUNNER
from research_os.runner.ssh import RUNNER as SSH_RUNNER

_RUNNER_REGISTRY: dict[str, Runner] = {
    LOCAL_RUNNER.name: LOCAL_RUNNER,
    SSH_RUNNER.name: SSH_RUNNER,
    SLURM_RUNNER.name: SLURM_RUNNER,
}


def runner_backends() -> tuple[str, ...]:
    return tuple(_RUNNER_REGISTRY)


def get_runner(name: str) -> Runner:
    return _RUNNER_REGISTRY[name]


__all__ = ["Runner", "get_runner", "runner_backends"]
