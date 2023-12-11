from datetime import date, timedelta
from itertools import islice
from typing import cast

from cal import Calendar
from magic import Item
from tenor import Tenor


def is_date_gen(obj):
    return isinstance(obj, DateGenerator)


def make_date(obj):
    if isinstance(obj, DateGenerator):
        return obj
    if isinstance(obj, date):
        return obj
    if isinstance(obj, str):
        return date.fromisoformat(obj)
    if isinstance(obj, (tuple, list)):
        return type(obj)(make_date(d) for d in obj)
    return None


def make_date_gen(obj):
    if isinstance(obj, DateGenerator):
        return obj
    if isinstance(obj, date):
        return ConstDateGenerator(obj)
    if isinstance(obj, str):
        return ConstDateGenerator(date.fromisoformat(obj))
    if isinstance(obj, (tuple, list)):
        return SequenceDateGenerator(make_date(obj))

def is_negative_slice(item):
    return item.start is not None and item.start < 0 \
        or item.stop is not None and item.stop < 0 \
        or item.step is not None and item.step < 0


class DateGenerator(Item):
    def __call__(self, input_date=None, start: date = date.min, end: date = date.max, after: date = date.min,
                 before: date = date.max, calendar: Calendar = None):
        return self.__invoke__(start, end, after, before, calendar)

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        raise StopIteration

    def is_signle_date_gen(self):
        return False

    def cadence(self):
        return None

    def __iter__(self):
        return self

    def __or__(self, other):
        return JoinDateGenerator(self, make_date_gen(other))

    def __ror__(self, other):
        return JoinDateGenerator(make_date_gen(other), self)

    def __and__(self, other):
        return CommonDatesDateGenerator(self, make_date_gen(other))

    def __rand__(self, other):
        return CommonDatesDateGenerator(make_date_gen(other), self)

    def __gt__(self, other):
        if not is_date_gen(other):
            return AfterDateGenerator(self, make_date(other))
        elif other.is_single_date_gen():
            return AfterDateGenerator(self, other)
        else:
            raise ValueError('Comparing two dage generators is not supported')

    def __lt__(self, other):
        if is_date_gen(other) and self.is_single_date_gen():
            return other.__ge__(self)
        else:
            if lhs := getattr(self, '__compared__', None):
                return BeforeDateGenerator(lhs, make_date(other))
            return BeforeDateGenerator(self, make_date(other))

    def __ge__(self, other):
        if not is_date_gen(other):
            return AfterOrOnDateGenerator(self, make_date(other))
        elif other.is_single_date_gen():
            return AfterOrOnDateGenerator(self, other)
        else:
            raise ValueError('Comparing two dage generators is not supported')

    def __le__(self, other):
        if is_date_gen(other) and self.is_single_date_gen():
            return other.__gt__(self)
        else:
            if lhs := getattr(self, '__compared__', None):
                return BeforeOrOnDateGenerator(lhs, make_date(other))
            return BeforeOrOnDateGenerator(self, make_date(other))

    def __add__(self, other):
        return AddTenorDateGenerator(self, Tenor(other))

    def __sub__(self, other):
        return SubTenorDateGenerator(self, Tenor(other))

    def __getitem__(self, item):
        if isinstance(item, int):
            if item >= 0:
                return SliceDateGenerator(self, slice(item, item + 1))
            else:
                raise ValueError(f"{type(self)} date generator does not support negative indices")
        if isinstance(item, slice):
            if is_negative_slice(item):
                raise ValueError(f"{type(self)} date generator does not support negative indices")
            return SliceDateGenerator(self, item)


class ConstDateGenerator(DateGenerator):
    def __init__(self, date):
        self.date = date

    def is_signle_date_gen(self):
        return True

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        yield self.date


class SequenceDateGenerator(DateGenerator):
    def __init__(self, dates):
        self.dates = dates

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        yield from self.dates


class AfterDateGenerator(DateGenerator):
    def __init__(self, gen, date):
        self.gen = gen
        self.date = date

    def cadence(self):
        return self.gen.cadence()

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        if is_date_gen(self.date):
            after = self.date(start, end, after, before, calendar)
        else:
            after = self.date

        yield from (d for d in self.gen.__invoke__(start, end, after, before, calendar) if d > after)

    def __bool__(self):
        if is_date_gen(self.date):
            self.date.__compared__ = self
        self.gen.__compared__ = self
        return True


class AfterOrOnDateGenerator(DateGenerator):
    def __init__(self, gen, date):
        self.gen = gen
        self.date = date

    def cadence(self):
        return self.gen.cadence()

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        if is_date_gen(self.date):
            after = self.date(start, end, after, before, calendar)
        else:
            after = self.date

        yield from (d for d in self.gen.__invoke__(start, end, after, before, calendar) if d >= after)

    def __bool__(self):
        if is_date_gen(self.date):
            self.date.__compared__ = self
        self.gen.__compared__ = self
        return True


class BeforeDateGenerator(DateGenerator):
    def __init__(self, gen, date):
        self.gen = gen
        self.date = date

    def cadence(self):
        return self.gen.cadence()

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        if is_date_gen(self.date):
            before = self.date(start, end, after, before, calendar)
        else:
            before = self.date

        yield from (d for d in self.gen.__invoke__(start, end, after, before, calendar) if d < before)


class BeforeOrOnDateGenerator(DateGenerator):
    def __init__(self, gen, date):
        self.gen = gen
        self.date = date

    def cadence(self):
        return self.gen.cadence()

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        if is_date_gen(self.date):
            before = self.date(start, end, after, before, calendar)
        else:
            before = self.date

        yield from (d for d in self.gen.__invoke__(start, end, after, before, calendar) if d <= before)


class EveryDayDateGenerator(DateGenerator):
    def cadence(self):
        return Tenor('1d')

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        start = start if start is not date.min else after
        end = end if end is not date.max else before

        while start <= end:
            yield start
            start += timedelta(days=1)


days = EveryDayDateGenerator()


class WeekdaysDateGenerator(DateGenerator):
    def __init__(self, gen):
        self.gen = gen

    def cadence(self):
        return self.gen.cadence()

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        we = calendar.weekend_days() if calendar else (5, 6)
        yield from (d for d in
                    self.gen.__invoke__(start, end, after, before, calendar)
                    if d.weekday() not in we)

    def __call__(self, gen):
        return WeekdaysDateGenerator(gen)


weekdays = WeekdaysDateGenerator(days)


class WeekendsDateGenerator(DateGenerator):
    def __init__(self, gen):
        self.gen = gen

    def cadence(self):
        return self.gen.cadence()

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        we = calendar.weekend_days() if calendar else (5, 6)
        yield from (d for d in
                    self.gen.__invoke__(start, end, after, before, calendar)
                    if d.weekday() in we)

    def __call__(self, gen):
        return WeekendsDateGenerator(gen)


weekends = WeekendsDateGenerator(EveryDayDateGenerator())


class WeeksDateGenerator(DateGenerator):
    def cadence(self):
        return Tenor('1w')

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        start = start if start is not date.min else after
        end = end if end is not date.max else before

        monday = start + timedelta(days=7 - start.weekday()) if start.weekday() > 0 else start
        while monday <= end:
            yield monday
            monday += timedelta(days=7)

    @property
    def mon(self):
        return self

    @property
    def tue(self):
        return self + '1d'

    @property
    def wed(self):
        return self + '2d'

    @property
    def thu(self):
        return self + '3d'

    @property
    def fri(self):
        return self + '4d'

    @property
    def sat(self):
        return self + '5d'

    @property
    def sun(self):
        return self + '6d'


weeks = WeeksDateGenerator()


class AddTenorDateGenerator(DateGenerator):
    def __init__(self, gen, tenor):
        self.gen = gen
        self.tenor = tenor

    def cadence(self):
        return self.gen.cadence()

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        start = start if start is not date.min else after
        start = self.tenor.sub_from(start, calendar) if not self.tenor.is_neg() else start
        yield from (self.tenor.add_to(d, calendar) for d in self.gen.__invoke__(start, end, after, before, calendar))


class SubTenorDateGenerator(DateGenerator):
    def __init__(self, gen, tenor):
        self.gen = gen
        self.tenor = tenor

    def cadence(self):
        return self.gen.cadence()

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        end = end if end is not date.max else before
        if end is not date.max:
            end = self.tenor.add_to(end, calendar) if not self.tenor.is_neg() else end
        yield from (self.tenor.sub_from(d, calendar) for d in self.gen.__invoke__(start, end, after, before, calendar))


class JoinDateGenerator(DateGenerator):
    def __init__(self, gen1, gen2):
        self.gen1 = gen1
        self.gen2 = gen2

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        g1 = self.gen1.__invoke__(start, end, after, before, calendar)
        g2 = self.gen2.__invoke__(start, end, after, before, calendar)

        d1 = next(g1, None)
        d2 = next(g2, None)
        while d1 is not None or d2 is not None:
            if d1 is None:
                yield d2
                while (d2 := next(g2, None)) is not None:
                    yield d2
            elif d2 is None:
                yield d1
                while (d1 := next(g1, None)) is not None:
                    yield d1
            elif d1 == d2:
                yield d1
                d1 = next(g1, None)
                d2 = next(g2, None)
            elif d1 < d2:
                yield d1
                d1 = next(g1, None)
            else:
                yield d2
                d2 = next(g2, None)


class CommonDatesDateGenerator(DateGenerator):
    def __init__(self, gen1, gen2):
        self.gen1 = gen1
        self.gen2 = gen2

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        g1 = self.gen1.__invoke__(start, end, after, before, calendar)
        g2 = self.gen2.__invoke__(start, end, after, before, calendar)

        d1 = next(g1, None)
        d2 = next(g2, None)
        while d1 is not None and d2 is not None:
            if d1 == d2:
                yield d1
                d1 = next(g1, None)
                d2 = next(g2, None)
            elif d1 < d2:
                d1 = next(g1, None)
            else:
                d2 = next(g2, None)


class MonthsDateGenerator(DateGenerator):
    def cadence(self):
        return Tenor('1m')

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        start = start if start is not date.min else after
        end = end if end is not date.max else before

        first = date(start.year, start.month, 1)
        while first <= end:
            yield first
            year = first.year + first.month // 12
            month = first.month % 12 + 1
            first = date(year, month, 1)

    @property
    def end(self):
        return months - '1d'

    @property
    def weeks(self):
        return SubSequenceDateGenerator(self, weeks)

    @property
    def days(self):
        return SubSequenceDateGenerator(self, days)

    @property
    def weekdays(self):
        return SubSequenceDateGenerator(self, weekdays)

    @property
    def weekends(self):
        return SubSequenceDateGenerator(self, weekends)


months = MonthsDateGenerator()


class SubSequenceDateGenerator(DateGenerator):
    def __init__(self, main_sequence, sub_sequence, slice = None):
        if main_sequence.cadence() in (None, Tenor('1d')):
            raise ValueError(f'cannot generate sub sequences from main sequence with cadence of {main_sequence.cadence()}')

        self.main_sequence = main_sequence
        self.sub_sequence = sub_sequence
        self.slice = slice

    def __getattr__(self, name):
        if isinstance(pr := getattr(type(self.sub_sequence),name),property):
            return pr.fget(self)

    def cadence(self):
        return self.sub_sequence.cadence()

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        for begin in self.main_sequence.__invoke__(start, end, after, before, calendar):
            end = self.main_sequence.cadence().add_to(begin)
            sub_sequence = cast(DateGenerator, begin <= self.sub_sequence < end)
            if self.slice is None:
                yield from sub_sequence()
            else:
                if is_negative_slice(self.slice):
                    yield from [d for d in sub_sequence()][self.slice]
                else:
                    yield from islice(sub_sequence(), self.slice.start, self.slice.stop, self.slice.step)

    def __getitem__(self, item):
        if isinstance(item, int):
            return SubSequenceDateGenerator(self.main_sequence, self.sub_sequence, slice(item, item + 1))
        if isinstance(item, slice):
            return SubSequenceDateGenerator(self.main_sequence, self.sub_sequence, item)

class DaysOfMonthDateGenerator(DateGenerator):
    def __init__(self, months, days):
        self.months = months
        self.days = days

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        for month in self.months.__invoke__(start, end, after, before, calendar):
            next_month = Tenor('1m').add_to(month)
            yield from (month <= self.days < next_month)()


class YearsDateGenerator(DateGenerator):
    def cadence(self):
        return Tenor('1y')

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        start = start if start is not date.min else after
        end = end if end is not date.max else before

        first = date(start.year, 1, 1)
        while first <= end:
            yield first
            first = date(first.year + 1, 1, 1)

    @property
    def end(self):
        return years - '1d'

    @property
    def months(self):
        return SubSequenceDateGenerator(self, months)

    @property
    def weeks(self):
        return SubSequenceDateGenerator(self, weeks)

    @property
    def days(self):
        return SubSequenceDateGenerator(self, days)

    @property
    def weekdays(self):
        return SubSequenceDateGenerator(self, weekdays)

    @property
    def weekends(self):
        return SubSequenceDateGenerator(self, weekends)


years = YearsDateGenerator()


class SliceDateGenerator(DateGenerator):
    def __init__(self, gen, slice):
        self.gen = gen
        self.slice = slice

    def cadence(self):
        return self.gen.cadence()

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        yield from islice(self.gen.__invoke__(start, end, after, before, calendar), self.slice.start, self.slice.stop, self.slice.step)
