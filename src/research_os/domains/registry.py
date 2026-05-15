from research_os.domains.generative import DOMAIN as GENERATIVE_DOMAIN
from research_os.domains.multimodal import DOMAIN as MULTIMODAL_DOMAIN
from research_os.domains.world_model import DOMAIN as WORLD_MODEL_DOMAIN

DOMAIN_REGISTRY: dict[str, dict[str, object]] = {
    MULTIMODAL_DOMAIN["name"]: MULTIMODAL_DOMAIN,
    GENERATIVE_DOMAIN["name"]: GENERATIVE_DOMAIN,
    WORLD_MODEL_DOMAIN["name"]: WORLD_MODEL_DOMAIN,
}


def domain_names() -> tuple[str, ...]:
    return tuple(DOMAIN_REGISTRY)


def get_domain(name: str) -> dict[str, object]:
    return DOMAIN_REGISTRY[name]
