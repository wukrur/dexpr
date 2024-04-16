import operator
from abc import abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from functools import reduce
from typing import Tuple, ForwardRef, TypeVar

from dexpr import ExprClass
from dexpr.dimension import Dimension
from dexpr.unit_system import UnitSystem

NUMBER = TypeVar('NUMBER', int, float, Decimal)

@dataclass(frozen=True, kw_only=True)
class Unit(ExprClass):
    name: str = None
    dimension: Dimension

    def __str__(self):
        return self.name

    def convert(self, value: NUMBER, to: 'Unit') -> NUMBER:
        if to is self:
            return value

        assert self.dimension is to.dimension  # for now, until context conversion factors are introduced
        return self.do_convert_to(value, to)

    @abstractmethod
    def do_convert_to(self, value: NUMBER, to: 'Unit') -> NUMBER: ...


@dataclass(frozen=True)
class PrimaryUnit(Unit):
    ratio: Decimal = Decimal(1)

    def __new__(cls, name=None, dimension: Dimension = None):
        if d := UnitSystem.instance().__primary_units__.get(name):
            assert d.dimension is dimension
            return d

        n = super().__new__(cls)
        object.__setattr__(n, 'dimension', dimension)
        object.__setattr__(n, 'name', name)
        UnitSystem.instance().__primary_units__[name] = n
        return n

    def __pow__(self, power, modulo=None):
        return ComplexUnit(components=((self, 2),))

    def __mul__(self, other):
        if isinstance(other, (PrimaryUnit, DerivedUnit)):
            components = defaultdict(int, ((other, 1),))
        elif isinstance(other, ComplexUnit):
            components = other.components
        else:
            raise ValueError(f"cannot multiply {self} and {other}")

        components[self] += 1
        return ComplexUnit(components=tuple(components.items()))

    def __truediv__(self, other):
        if isinstance(other, (PrimaryUnit, DerivedUnit)):
            components = defaultdict(int, ((other, -1),))
        elif isinstance(other, ComplexUnit):
            components = defaultdict(int, ((d, -p) for d, p in other.components))
        else:
            raise ValueError(f"cannot divide {self} and {other}")

        components[self] += 1
        return ComplexUnit(components=tuple(components.items()))

    def do_convert_to(self, value: NUMBER, to: 'Unit') -> NUMBER:
        if isinstance(to, OffsetDerivedUnit):
            return value / type(value)(to.ratio) - type(value)(to.offset)
        elif isinstance(to, DerivedUnit):
            return value / type(value)(to.ratio)

        assert False, f'conversion from {self} to {to} is not supported'


@dataclass(frozen=True, kw_only=True)
class DerivedUnit(Unit):
    primary_unit: Unit
    ratio: Decimal
    dimension: Dimension = lambda s: s.primary_unit.dimension

    def __new__(cls, primary_unit: Unit | ForwardRef("Quantity"), ratio: Decimal = Decimal(1), name=None):
        from .quantity import Quantity
        if type(primary_unit) is Quantity:
            primary_unit = primary_unit.unit
            ratio = primary_unit.value

        if type(primary_unit) is DerivedUnit:
            primary_unit = primary_unit.primary_unit
            ratio *= primary_unit.ratio

        if d := UnitSystem.instance().__derived_units__.get((primary_unit, ratio)):
            return d

        n = super().__new__(cls)
        object.__setattr__(n, 'primary_unit', primary_unit)
        object.__setattr__(n, 'ratio', ratio)
        if name:
            object.__setattr__(n, 'name', name)
        UnitSystem.instance().__derived_units__[(primary_unit, ratio)] = n
        return n

    def __pow__(self, power, modulo=None):
        return ComplexUnit(components=((self, 2),))

    def __mul__(self, other):
        if isinstance(other, (PrimaryUnit, DerivedUnit)):
            components = defaultdict(int, ((other, 1),))
        elif isinstance(other, ComplexUnit):
            components = other.components
        else:
            raise ValueError(f"cannot multiply {self} and {other}")

        components[self] += 1
        return ComplexUnit(components=tuple(components.items()))

    def __truediv__(self, other):
        if isinstance(other, (PrimaryUnit, DerivedUnit)):
            components = defaultdict(int, ((other, -1),))
        elif isinstance(other, ComplexUnit):
            components = defaultdict(int, ((d, -p) for d, p in other.components))
        else:
            raise ValueError(f"cannot divide {self} and {other}")

        components[self] += 1
        return ComplexUnit(components=tuple(components.items()))

    def do_convert_to(self, value: NUMBER, to: 'Unit') -> NUMBER:
        primary_value = value * type(value)(self.ratio)
        if to is not self.primary_unit:
            return self.primary_unit.do_convert_to(primary_value, to)
        else:
            return primary_value


@dataclass(frozen=True, kw_only=True)
class OffsetDerivedUnit(DerivedUnit):
    offset: Decimal

    def __new__(cls, primary_unit: Unit | ForwardRef("Quantity"), ratio: Decimal = Decimal(1), offset: Decimal = Decimal(0), name=None):
        if type(primary_unit) is DerivedUnit:
            primary_unit = primary_unit.primary_unit
            ratio *= primary_unit.ratio

        if d := UnitSystem.instance().__derived_units__.get((primary_unit, ratio, offset)):
            return d

        n = super().__new__(cls)
        object.__setattr__(n, 'primary_unit', primary_unit)
        object.__setattr__(n, 'scaling_factor', ratio)
        object.__setattr__(n, 'offset', offset)
        if name:
            object.__setattr__(n, 'name', name)
        UnitSystem.instance().__derived_units__[(primary_unit, ratio, offset)] = n
        return n

    def do_convert_to(self, value: NUMBER, to: 'Unit') -> NUMBER:
        primary_value = (value + type(value)(self.offset)) / type(value)(self.scaling_factor)
        if to is not self.primary_unit:
            return self.primary_unit.do_convert_to(primary_value, to)
        else:
            return primary_value


@dataclass(frozen=True, kw_only=True)
class ComplexUnit(Unit):
    components: Tuple[Tuple[Unit, int], ...]
    dimension: Dimension = lambda s: reduce(operator.mul, (u.dimension**m for u, m in s.components))
    ratio: Decimal = lambda s: reduce(operator.mul, (pow(u.ratio, m) for u, m in s.components))

    def __new__(cls, components, name=None):
        if d := UnitSystem.instance().__complex_units__.get(components):
            return d

        n = super().__new__(cls)
        object.__setattr__(n, 'components', components)
        if name:
            object.__setattr__(n, 'name', name)
        UnitSystem.instance().__complex_units__[components] = n
        return n

    def __post_init__(self):
        if not self.name:
            up = '*'.join(f"{d}**{p}" if p != 1 else str(d) for d, p in self.components if p > 0) or '1'
            dn = ('*'.join(f"{d}**{abs(p)}" if p != -1 else str(d) for d, p in self.components if p < 0))
            dn = ('/' + dn) if dn else ''
            object.__setattr__(self, 'name', up + dn)

    def __mul__(self, other):
        if isinstance(other, (PrimaryUnit, DerivedUnit)):
            components = defaultdict(int, ((other, 1),))
        elif isinstance(other, ComplexUnit):
            components = other.components
        else:
            raise ValueError(f"cannot multiply {self} and {other}")

        for u, p in self.components:
            components[u] += p

        return ComplexUnit(components=tuple(components.items()))

    def __truediv__(self, other):
        if isinstance(other, (PrimaryUnit, DerivedUnit)):
            components = defaultdict(int, ((other, -1),))
        elif isinstance(other, ComplexUnit):
            components = defaultdict(int, ((d, -p) for d, p in other.components))
        else:
            raise ValueError(f"cannot divide {self} and {other}")

        for u, p in self.components:
            components[u] += p

        return ComplexUnit(components=tuple(components.items()))

    def do_convert_to(self, value: NUMBER, to: 'ComplexUnit') -> NUMBER:
        return type(value)(self.ratio / to.ratio) * value
