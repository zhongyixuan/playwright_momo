"""
Shared test utils, pure finctions.
"""

from __future__ import annotations
import re
from typing import List

def majority_contain_keyword(names: List[str], keyword: str, threshold: float = 0.5) -> bool:
    """
    Return True when more than *threshold* fraction of results contain
    the keyword. Useful for relevance checks where 100% isn't realistic.
    """
    if not names:
        return False
    kw = keyword.lower()
    hits = sum(1 for n in names if kw in n.lower())
    return (hits / len(names)) >= threshold