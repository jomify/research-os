from dataclasses import dataclass


@dataclass(frozen=True)
class Runner:
    name: str
    description: str
