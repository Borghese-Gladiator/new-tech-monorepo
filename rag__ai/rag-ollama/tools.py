# tools.py
from datetime import datetime

def get_time(timezone: str = "UTC") -> str:
    """Return current time for a timezone label (simple demo)."""
    # For demo, ignore timezone and return UTC now
    return datetime.utcnow().isoformat() + "Z"

def simple_calc(a: int, b: int, op: str = "add") -> int:
    if op == "add":
        return a + b
    if op == "mul":
        return a * b
    raise ValueError("op must be add or mul")
