def infer_domain_hints(prompt: str) -> list[str]:
    lowered = prompt.lower()
    hints: list[str] = []
    if "world model" in lowered or "world-model" in lowered or "\u4e16\u754c\u6a21\u578b" in prompt:
        hints.append("world_model")
    if "diffusion" in lowered or "generat" in lowered or "\u751f\u6210\u6a21\u578b" in prompt:
        hints.append("generative")
    if "multimodal" in lowered or "vqa" in lowered or "\u591a\u6a21\u6001" in prompt:
        hints.append("multimodal")
    return hints
