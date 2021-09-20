# from collections.abc import Iterable
# from typing import TypeVar, Optional

# T = TypeVar("T")

# def head(ls: Iterable[T]) -> Optional[T]:
#     return next(iter(ls), None)


def parse_timestamp(t_str: str) -> float:
    """
    >>> parse_timestamp("00:01:38.970")
    98.97
    """
    h, m, s = t_str.split(":")
    return (int(h) * 60 + int(m)) * 60 + float(s)
