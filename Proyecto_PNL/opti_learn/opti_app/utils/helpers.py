from __future__ import annotations

from typing import Any


def to_float_list(x: Any):
    try:
        return [float(v) for v in x]
    except Exception:
        return []

