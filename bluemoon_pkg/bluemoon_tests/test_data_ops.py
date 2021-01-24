from bluemoon import get_aggregate_data
from datetime import datetime
from bluemoon.models import Day, Dataset

def test_day_key():
    today = datetime.utcnow()
    d1 = Day(day_dt=today)
    d2 = Day(year=today.year, month=today.month, day=today.day)
    d3 = Day(day_as_str=Day.get_today())

    assert d1.day_as_dt == d2.day_as_dt == d3.day_as_dt
    assert d1.day_as_str == d2.day_as_str == d3.day_as_str ==\
        d1.key == d2.key == d3.key
