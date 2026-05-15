from research_os.runner import get_runner, runner_backends
from research_os.domains import DOMAIN_REGISTRY, domain_names, get_domain


def test_runner_registry_exposes_first_version_backends() -> None:
    assert runner_backends() == ("local", "ssh", "slurm")
    assert get_runner("local").name == "local"
    assert get_runner("ssh").name == "ssh"
    assert get_runner("slurm").name == "slurm"


def test_domain_registry_exposes_first_version_domains() -> None:
    assert domain_names() == ("multimodal", "generative", "world_model")
    assert DOMAIN_REGISTRY["generative"]["default_metrics"] == ["fid", "clip_score"]
    assert get_domain("world_model")["label"] == "World Model"
