from dataclasses import dataclass

from dexpr.dataclassex import DataclassEx, dataclassex, OpDescriptor
from dexpr.magic import ParameterOp

Self = ParameterOp(_name='Self', _index=0)


def test_expr_descriptor():
    @dataclass
    class expr_1:
        a: int
        b: int = OpDescriptor(Self.a + 1)

    e = expr_1(a=2)
    assert e.b == 3

    e = expr_1(a=2, b=12)
    assert e.b == 12


def test_expr_descriptor_implicit():
    @dataclass
    class expr_1(DataclassEx):
        a: int
        b: int = Self.a + 1

    e = expr_1(a=2)
    assert e.b == 3

    e = expr_1(a=2, b=12)
    assert e.b == 12


def test_dataclassex():
    @dataclassex
    class expr_1:
        Self: "expr_1"

        a: int
        b: int = Self.a + 1

    e = expr_1(a=2)
    assert e.b == 3

    e = expr_1(a=2, b=12)
    assert e.b == 12
