from decimal import Decimal

from dexpr.dimension import PrimaryDimension, DerivedDimension
from dexpr.unit import PrimaryUnit, DerivedUnit
from dexpr.unit_system import UnitSystem


def test_units():
    with UnitSystem():
        length = PrimaryDimension(name='length')
        area = DerivedDimension(name='area', components=((length, 2),))
        meter = PrimaryUnit(name='meter', dimension=length)
        meter_sq = meter**2
        assert meter_sq.name == 'meter**2'
        assert meter_sq.dimension is area

        force = PrimaryDimension(name='force')
        newton = PrimaryUnit(name='newton', dimension=force)

        pressure = DerivedDimension(name='pressure', components=((force, 1), (area, -1)))
        pascal = newton / meter**2
        assert pascal.name == 'newton/meter**2'
        assert pascal.dimension is pressure
        assert pascal is newton / meter_sq


def test_unit_auto_naming():
    with UnitSystem() as U:
        U.length = PrimaryDimension()
        U.area = U.length**2
        U.meter = PrimaryUnit(dimension=U.length)
        meter_sq = U.meter**2
        assert meter_sq.name == 'meter**2'
        assert meter_sq.dimension is U.area

        U.meter_sq = meter_sq
        assert meter_sq.name == 'meter_sq'

        U.force = PrimaryDimension()
        U.newton = PrimaryUnit(dimension=U.force)

        U.pressure = U.force / U.area
        U.pascal = U.newton / U.meter**2
        assert U.pascal.name == 'pascal'
        assert U.pascal.dimension is U.pressure
        assert U.pascal is U.newton / U.meter_sq


def test_unit_conversion_1():
    with UnitSystem() as U:
        U.length = PrimaryDimension()
        U.meter = PrimaryUnit(dimension=U.length)
        U.cm = DerivedUnit(primary_unit=U.meter, ratio=Decimal('0.01'))

        assert U.cm.convert(100., to=U.meter) == 1.
        assert U.cm.convert(Decimal(100), to=U.meter) == 1.

        assert U.meter.convert(100., to=U.cm) == 10000.

        U.meter_sq = U.meter**2
        U.cm_sq = U.cm**2

        assert U.meter_sq.convert(1., to=U.cm_sq) == 10000.
        assert U.cm_sq.convert(1., to=U.meter_sq) == 0.0001

        U.timespan = PrimaryDimension()
        U.second = PrimaryUnit(dimension=U.timespan)
        U.minute = DerivedUnit(primary_unit=U.second, ratio=Decimal(60))

        U.velocity = U.length / U.timespan

        assert (U.meter/U.second).convert(1., to=U.cm / U.minute) == 6000.
        assert (U.cm/U.second).convert(1., to=U.meter / U.minute) == 60. / 100.
