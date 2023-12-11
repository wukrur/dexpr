from datetime import date

from magic import Item


class Calendar:
    pass


class Tenor:
    pass


def make_date(obj):
    if isinstance(obj, DateGenerator):
        return obj
    if isinstance(obj, date):
        return ConstDateGenerator(obj)
    if isinstance(obj, str):
        return make_date(date.fromisoformat(obj))
    if isinstance(obj, (tuple, list)):
        return SequenceDateGenerator(obj)


class DateGenerator(Item):
    def __call__(self, input_date=None, start: date = date.min, end: date = date.max, after: date = date.min,
                 before: date = date.max, calendar: Calendar = None):
        return self.__invoke__(start, end, after, before, calendar)

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        raise StopIteration

    def __iter__(self):
        return self

    def __or__(self, other):
        pass

    def __ror__(self, other):
        pass

    def __gt__(self, other):
        pass

    def __lt__(self, other):
        pass

    def __ge__(self, other):
        pass

    def __le__(self, other):
        pass

    def __add__(self, other):
        pass

    def __sub__(self, other):
        pass

    def __getitem__(self, item):
        pass


class ConstDateGenerator(DateGenerator):
    def __init__(self, date):
        self.date = date

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        yield self.date


class SequenceDateGenerator:
    def __init__(self, dates):
        self.dates = dates

    def __invoke__(self, start: date = date.min, end: date = date.max, after: date = date.min, before: date = date.max,
                   calendar: Calendar = None):
        yield from self.dates
