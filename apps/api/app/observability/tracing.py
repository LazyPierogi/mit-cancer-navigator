from __future__ import annotations

from functools import wraps
from time import perf_counter


def traced(name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = perf_counter()
            result = func(*args, **kwargs)
            elapsed_ms = int((perf_counter() - start) * 1000)
            return result, {"spanName": name, "elapsedMs": elapsed_ms}

        return wrapper

    return decorator

