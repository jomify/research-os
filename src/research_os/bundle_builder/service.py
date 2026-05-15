from research_os.models.brief import ResearchBrief
from research_os.models.bundle import PaperBundle
from research_os.models.evidence import EvidenceLedger
from research_os.web_research.service import build_live_evidence, build_stub_evidence


def build_bundle(brief: ResearchBrief, live: bool = False) -> PaperBundle:
    evidence: EvidenceLedger
    if live:
        evidence = build_live_evidence(brief)
    else:
        evidence = build_stub_evidence(brief)
    return PaperBundle.from_brief(brief=brief, evidence=evidence)
