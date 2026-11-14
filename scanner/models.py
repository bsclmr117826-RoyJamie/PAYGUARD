"""Shared data structures for the PayGuard rule engine."""
from dataclasses import dataclass, asdict
from typing import Callable

# A "hit" is what a rule's check function returns: (line_number, evidence_text)
Hit = tuple[int, str]


@dataclass(frozen=True)
class Finding:
    """One security finding. Field names mirror the Finding class in the class diagram."""
    rule_code: str
    title: str
    severity: str          # Critical / High / Medium / Low
    pillar: str            # SITF pillar (filled in by the SITF mapper)
    technique: str         # SITF technique (filled in by the SITF mapper)
    file_path: str
    line_number: int
    masked_evidence: str   # secrets are masked: only the first 4 characters are kept
    status: str = "open"   # open / accepted-risk / fixed

    def to_dict(self) -> dict:
        """Plain dictionary, handy for saving through the Django ORM."""
        return asdict(self)


@dataclass(frozen=True)
class Rule:
    """A detection rule: where it applies and how it checks a file's text."""
    code: str
    title: str
    severity: str
    applies_to: Callable[[str], bool]     # takes a file path, returns True/False
    check: Callable[[str], list[Hit]]     # takes file text, returns a list of hits
