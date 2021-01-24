from datetime import datetime, timedelta
import pandas as pd
import json
import ephem
import calendar

def parse_day(day_as_str):
    pieces = day_as_str.split("-")
    return int(pieces[0]), int(pieces[1]), int(pieces[2])

def str_to_day(day_as_str):
    return datetime(*parse_day(day_as_str))

def compound_field_name(field_name, subfield):
    return "{}_{}".format(field_name, subfield)

class Dataset:

    def count_cumulative_entries(self, field):
        n = 0
        for day in self.days.values():
            if day.cumulative.get(field):
                n += len(day.cumulative.get(field))
        return n

    def update(self, immutable_dataset):
        days_affected = []
        # The self object will be updated with values from immutable_dataset
        for key, d in self.days.items():
            other_day = immutable_dataset.days.get(key)
            if other_day and d.update(other_day, overwrite_fields=True):
                days_affected.append(key)
        for key, d in immutable_dataset.days.items():
            if not self.days.get(key):
                days_affected.append(key)
                self.days[key] = d
        return days_affected

    def __init__(self, today=None):
        """
        When today is not explicitly set, datetime.today() will be used
        """
        self.days = dict()
        self._ready = False
        if today:
            assert type(today) == datetime
            self.today = today
        else:
            self.today = datetime.today()
            self.today = datetime(self.today.year, self.today.month, self.today.day)

        self.dataset_analyses = dict(
            availability=Dataset.calculate_data_availability,
            days_before=self.calculate_days_before
        )

    def add_dataset_analysis(self, field_name, analysis_function):
        """
        Have a field name to bind the result to; if result is itself a dict,
        that many filds will be added with the field_name as prefix.
        Analysis function should expect all days as a dict, and should
        provide a dict of values or a dict of dicts of values.
        """
        if analysis_function is not None:
            self.dataset_analyses[field_name] = analysis_function

    def add(self, day, overwrite_fields):
        if self.days.get(day.key):
            self.days[day.key].update(day, overwrite_fields)
        else:
            self.days[day.key] = day

    def drop_field(self, field_name):
        for day in self.days.values():
            day.drop_field(field_name)

    def create_field(self, field_name, values_by_day):
        for key, day in self.days.items():
            if type(values_by_day.get(key)) == dict:
                for subfield, value in values_by_day.get(key).items():
                    day.set_value(
                        compound_field_name(field_name, subfield),
                        value
                    )
            else:
                day.set_value(field_name, values_by_day.get(key))

    @property
    def ready(self):
        return self._ready

    def set_ready(self, value):
        if value:
            for field_name, analysis_function in self.dataset_analyses.items():
                self.create_field(field_name, analysis_function(self.days))

            self._ready = True
        else:
            self._ready = False
            for field_name in self.dataset_analyses.keys():
                self.drop_field(field_name)

    @staticmethod
    def calculate_data_availability(all_days):
        data_availability = {}
        for key, day in all_days.items():
            data_availability[key] = data_availability.get(key, 0) + 1

            for other_day in [
                Day.get_key(day.day_as_dt + timedelta(days=1)),
                Day.get_key(day.day_as_dt - timedelta(days=1))
            ]:
                if other_day in all_days:
                    data_availability[other_day] = data_availability.get(other_day, 0) + 1/3
        return data_availability

    def calculate_days_before(self, all_days):
        return {key: (self.today - day.day_as_dt).days for key, day in all_days.items()}

    def asDataFrame(self):
        assert self.ready
        return pd.DataFrame([d.as_dict() for d in self.days.values()])

class Day:

    @staticmethod
    def get_today():
        return datetime.utcnow().strftime('%Y-%m-%d')

    @staticmethod
    def get_key(datetime):
        return datetime.strftime('%Y-%m-%d')

    def __init__(self, day_dt=None, year=None, month=None, day=None, day_as_str=None):
        if day_dt:
            year, month, day = day_dt.year, day_dt.month, day_dt.day
        elif day_as_str:
            year, month, day = parse_day(day_as_str)
        assert year and month and day
        self.day_as_dt = datetime(year, month, day)
        self.day_as_str = Day.get_key(self.day_as_dt)

        self.data = dict(
            moon=self._get_moon(),
            weekday_str=calendar.day_name[self.day_as_dt.weekday()],
            weekday_num=self.day_as_dt.weekday(),
            season=self._get_season()
        )
        self.cumulative = dict()

    @property
    def weekday_char(self):
        return "R" if self.data["weekday_str"] == "Thursday" else self.data["weekday_str"][0]

    def _get_moon(self):
        return min(
            (ephem.localtime(ephem.next_full_moon(self.day_as_dt)) - self.day_as_dt).days,
            (self.day_as_dt - ephem.localtime(ephem.previous_full_moon(self.day_as_dt))).days
        )

    def _get_season(self):
        return min(
            (ephem.localtime(ephem.next_equinox(self.day_as_dt)) - self.day_as_dt).days,
            (self.day_as_dt - ephem.localtime(ephem.previous_equinox(self.day_as_dt))).days,
            (ephem.localtime(ephem.next_solstice(self.day_as_dt)) - self.day_as_dt).days,
            (self.day_as_dt - ephem.localtime(ephem.previous_solstice(self.day_as_dt))).days
        )

    def drop_field(self, field_name):
        if field_name in self.data:
            del self.data[field_name]

    def set_value(self, field_name, value):
        self.data[field_name] = value

    def add_record(self, field_name, new_record):
        self.cumulative[field_name] = self.cumulative.get(field_name, [])
        self.cumulative[field_name].append(new_record)

    def has_data(self):
        return True

    def serialize(self, serialize_fields=[]):
        serialized_only = lambda dict_: {k:v for k, v \
            in dict_.items() if k in serialize_fields or not serialize_fields}
        return dict(
            data=serialized_only(self.data),
            cumulative=serialized_only(self.cumulative)
        )

    def as_dict(self):
        return dict(
            day_dt=self.day_as_dt,
            day_str=self.day_as_str,
            **self.data
        )

    @property
    def key(self):
        return self.day_as_str

    def update(self, other_day, overwrite_fields):
        overwritten = False
        for key, vs in other_day.cumulative.items():
            if overwrite_fields:
                if str(self.cumulative.get(key)) != str(vs):
                    overwritten = True
                self.cumulative[key] = vs
            else:
                self.cumulative[key] = self.cumulative.get(key, [])
                self.cumulative[key].extend(vs)

        for k, v in other_day.data.items():
            if self.data.get(k) != v:
                overwritten = True
            self.data[k] = v
        return overwritten

class AllData:

    def __init__(self):
        self.from_dict({})

    def set_serializable_field(self, field_name):
        self.meta["serialize_fields"].add(field_name)

    @classmethod
    def build(cls, db_target):
        all_data = cls()
        try:
            f = open(db_target)
            all_data.from_dict(json.load(f))
        except Exception as e:
            print(e)
            print("Created a new StorytellerDB.")
            with open(db_target, 'w', encoding='utf-8') as f:
                json.dump(all_data.as_dict(), f, ensure_ascii=False, indent=2)
        return all_data

    def from_dict(self, d):
        self.dataset = Dataset()
        for k, v in d.get("days", {}).items():
            day = Day(day_as_str=k)
            day.data = v.get("data", {})
            day.cumulative = v.get("cumulative", {})
            self.dataset.add(day, overwrite_fields=False)
        self.experiments = d.get("experiments", {})
        self.meta = d.get("meta", {})
        self.meta["serialize_fields"] = set(self.meta.get("serialize_fields", set()))
        self.changelog = d.get("changelog", [])

    def as_dict(self):
        meta_ = {k:v for k, v in self.meta.items()}
        meta_["serialize_fields"] = list(meta_.get("serialize_fields", []))
        days_ = {k: v.serialize(self.meta.get("serialize_fields")) for k, v in self.dataset.days.items()}
        return dict(
            days=days_,
            experiments=self.experiments,
            meta=meta_,
            changelog=self.changelog
        )

    def update(self, immutable_dataset, description):
        days_affected = self.dataset.update(immutable_dataset)
        if days_affected and description:
            self.changelog.append(dict(
                day=Day.get_today(),
                days_affected=days_affected,
                description=description
            ))
        return len(days_affected)
