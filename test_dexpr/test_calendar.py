from datetime import date

import pytest

from dexpr import weeks
from dexpr.calendar import WeekendCalendar, HolidayCalendar


@pytest.mark.parametrize(['d', 't', 'r'], (
        (date(1998, 2, 3), 1, date(1998, 2, 4)),
        (date(1998, 2, 3), 4, date(1998, 2, 9)),
        (date(1998, 2, 3), 5, date(1998, 2, 10)),
        (date(1998, 2, 3), 10, date(1998, 2, 17)),
        (date(1998, 2, 9), 5, date(1998, 2, 16)),
        (date(1998, 2, 7), 0, date(1998, 2, 9)),
        (date(1998, 2, 7), 5, date(1998, 2, 16)),
        (date(1998, 2, 7), 4, date(1998, 2, 13)),
))
def test_weekend_calendar_add_business_days(d, t, r):
    assert WeekendCalendar([5, 6]).add_business_days(d, t) == r

@pytest.mark.parametrize(['d', 't', 'r'], (
        (date(1998, 2, 3), 1, date(1998, 2, 2)),
        (date(1998, 2, 3), 4, date(1998, 1, 28)),
        (date(1998, 2, 3), 5, date(1998, 1, 27)),
        (date(1998, 2, 3), 10, date(1998, 1, 20)),
        (date(1998, 2, 9), 5, date(1998, 2, 2)),
        (date(1998, 2, 7), 0, date(1998, 2, 6)),
        (date(1998, 2, 7), 5, date(1998, 1, 30)),
        (date(1998, 2, 7), 4, date(1998, 2, 2)),
))
def test_weekend_calendar_sub_business_days(d, t, r):
    assert WeekendCalendar([5, 6]).sub_business_days(d, t) == r

@pytest.mark.parametrize(['d', 't', 'r'], (
        (date(1998, 2, 3), 1, date(1998, 2, 4)),
        (date(1998, 2, 3), 4, date(1998, 2, 10)),
        (date(1998, 2, 3), 5, date(1998, 2, 11)),
        (date(1998, 2, 3), 10, date(1998, 2, 19)),
        (date(1998, 2, 9), 5, date(1998, 2, 17)),
        (date(1998, 2, 7), 0, date(1998, 2, 9)),
        (date(1998, 2, 7), 5, date(1998, 2, 17)),
        (date(1998, 2, 7), 4, date(1998, 2, 16)),
))
def test_holiday_calendar_add_business_days(d, t, r):
    all_fridays = '1997-01-01' <= weeks.fri <= '1999-01-01'
    calendar = HolidayCalendar([5, 6], tuple(all_fridays()))
    assert calendar.add_business_days(d, t) == r

@pytest.mark.parametrize(['d', 't', 'r'], (
        (date(1998, 2, 3), 1, date(1998, 2, 4)),
        (date(1998, 2, 3), 4, date(1998, 2, 10)),
        (date(1998, 2, 3), 5, date(1998, 2, 11)),
        (date(1998, 2, 3), 10, date(1998, 2, 19)),
        (date(1998, 2, 9), 5, date(1998, 2, 18)),
        (date(1998, 2, 7), 0, date(1998, 2, 10)),
        (date(1998, 2, 7), 5, date(1998, 2, 18)),
        (date(1998, 2, 7), 4, date(1998, 2, 17)),
))
def test_holiday_calendar_add_business_days_1(d, t, r):
    all_mondays = '1997-01-01' <= weeks.mon <= '1999-01-01'
    calendar = HolidayCalendar([5, 6], tuple(all_mondays()))
    assert calendar.add_business_days(d, t) == r

@pytest.mark.parametrize(['d', 't', 'r'], (
        (date(1998, 2, 3), 1, date(1998, 2, 2)),
        (date(1998, 2, 3), 4, date(1998, 1, 27)),
        (date(1998, 2, 3), 5, date(1998, 1, 26)),
        (date(1998, 2, 3), 10, date(1998, 1, 15)),
        (date(1998, 2, 9), 5, date(1998, 1, 29)),
        (date(1998, 2, 7), 0, date(1998, 2, 5)),
        (date(1998, 2, 7), 5, date(1998, 1, 28)),
        (date(1998, 2, 7), 4, date(1998, 1, 29)),
))
def test_holiday_calendar_sub_business_days(d, t, r):
    all_fridays = '1997-01-01' <= weeks.fri <= '1999-01-01'
    calendar = HolidayCalendar([5, 6], tuple(all_fridays()))
    assert calendar.sub_business_days(d, t) == r


@pytest.mark.parametrize(['d', 't', 'r'], (
        (date(1998, 2, 3), 1, date(1998, 1, 30)),
        (date(1998, 2, 3), 4, date(1998, 1, 27)),
        (date(1998, 2, 3), 5, date(1998, 1, 23)),
        (date(1998, 2, 3), 10, date(1998, 1, 15)),
        (date(1998, 2, 9), 5, date(1998, 1, 29)),
        (date(1998, 2, 7), 0, date(1998, 2, 6)),
        (date(1998, 2, 7), 5, date(1998, 1, 29)),
        (date(1998, 2, 7), 4, date(1998, 1, 30)),
))
def test_holiday_calendar_sub_business_days_1(d, t, r):
    all_mondays = '1997-01-01' <= weeks.mon <= '1999-01-01'
    calendar = HolidayCalendar([5, 6], tuple(all_mondays()))
    assert calendar.sub_business_days(d, t) == r
