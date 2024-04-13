from dataclasses import dataclass

from dexpr.unit import Unit


@dataclass(frozen=True)
class Quantity:
    value: float
    unit: Unit

