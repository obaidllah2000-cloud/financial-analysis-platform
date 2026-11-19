"""Decimal helpers. All core arithmetic is Decimal; floats appear only at the JSON boundary."""
from decimal import Decimal, InvalidOperation, getcontext

getcontext().prec = 28

D0 = Decimal(0)


def D(x) -> Decimal | None:
    if x is None or x == "":
        return None
    if isinstance(x, Decimal):
        return x
    try:
        if isinstance(x, float):
            return Decimal(repr(x))
        s = str(x).strip().replace(",", "")
        neg = s.startswith("(") and s.endswith(")")
        if neg:
            s = s[1:-1]
        v = Decimal(s)
        return -v if neg else v
    except (InvalidOperation, ValueError):
        return None


def div(a: Decimal | None, b: Decimal | None) -> Decimal | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


def f(x: Decimal | None, places: int = 6) -> float | None:
    if x is None:
        return None
    return float(round(x, places))


def ssum(values) -> Decimal | None:
    vals = [v for v in values if v is not None]
    return sum(vals, D0) if vals else None
