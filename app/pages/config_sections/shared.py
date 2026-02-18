from __future__ import annotations

from typing import Dict


def merge_payload(
    base: Dict[str, object], updates: Dict[str, object]
) -> Dict[str, object]:
    payload = dict(base)
    payload.update(updates)
    return payload
