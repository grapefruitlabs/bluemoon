import textwrap
import json
from enum import Enum
from .models import Day, Dataset, str_to_day, compound_field_name
from . import get_aggregate_data
from datetime import timedelta


class DataSource(Enum):

    #INTERNAL
    eventlog = 'eventlog'
    worklog = 'worklog'
    datalog = 'datalog'
    report = 'report'

    # EXTERNAL
    fitbit = '*fitbit'
    oura = '*oura'
    toggl = '*toggl'
    exist = '*exist'
    lastfm = '*last.fm'

    def build_dataset(self, data, base_dataset=None):
        ds = Dataset()
        accumulator_params = {}

        if self in [DataSource.oura, DataSource.lastfm, DataSource.toggl]:
            for index, row in get_aggregate_data(data).iterrows():
                ds.add(self.build_day(row), overwrite_fields=[])

        elif self == DataSource.worklog:

            worklog_ = json.load(open(data))
            first_day = str_to_day(worklog_["first_day"])
            last_day = str_to_day(worklog_["last_day"])

            accumulator_params = {}

            day_cursor = first_day
            while day_cursor <= last_day:
                d = Day(day_dt=day_cursor)

                worktime = worklog_["working_hours"] if d.weekday_char in worklog_["working_days"] else 0
                if d.key in worklog_["exceptions"]:
                    worktime = int(worklog_["exceptions"][d.key])

                day_cursor += timedelta(days=1)
                d.set_value(str(self), worktime)
                ds.add(d, overwrite_fields=True)

        ds.add_dataset_analysis(str(self), self.get_accumulator(accumulator_params))
        return ds

    def get_filter(self):
        """
        How should data with a very large number of fields be filtered?
        """
        return None

    @staticmethod
    def _toggl_duration_parse(s):
        s = s.split(":")
        i = int(s[0]) * 60 + int(s[1])
        return i

    @staticmethod
    def _toggl_accumulator(days):
        ## Given days, provides a per-day analysis of work duration and variety
        result = dict()

        for key, d in days.items():
            vs = d.cumulative.get(str(DataSource.toggl), [])
            result[key] = dict()
            result[key]["ct"] = len(vs)
            result[key]["duration"] = sum([
                DataSource._toggl_duration_parse(v["Duration"]) for v in vs if v.get("Duration")
            ])
            result[key]["overwork"] = 0 if result[key]["duration"] <=11 else (
                1 if result[key]["duration"] <= 14 else 2
            )
        return result

    def get_accumulator(self, accumulator_params={}):
        """
        How should data with multiple records per day be accumulated?
        Expects the whole dataset and optional parameters, and constructs
        a values_by_day dict
        """

        if self == DataSource.toggl:
            return DataSource._toggl_accumulator
        return None

    def get_fields(self):
        if self == DataSource.toggl:
            return ["Project", "Task", "Description", "Start time",
            "Duration", "Tags"]
        elif self == DataSource.oura:
            return ("Sleep Score,Total Sleep Score,REM Sleep Score,"+\
                "Deep Sleep Score,Sleep Efficiency Score,Restfulness Score,"+\
                "Sleep Latency Score,Sleep Timing Score,Total Bedtime,"+\
                "Total Sleep Time,Awake Time,REM Sleep Time,Light Sleep Time,"+\
                "Deep Sleep Time,Restless Sleep,Sleep Efficiency,"+\
                "Sleep Latency,Sleep Timing,Sleep Timing,Bedtime Start,"+\
                "Bedtime End,Average Resting Heart Rate,"+\
                "Lowest Resting Heart Rate,Average HRV,"+\
                "Temperature Deviation (°C),Respiratory Rate,Activity Score,"+\
                "Stay Active Score,Move Every Hour Score,"+\
                "Meet Daily Targets Score,Training Frequency Score,"+\
                "Training Volume Score,Recovery Time Score,Activity Burn,"+\
                "Total Burn,Target Calories,Steps,Daily Movement,"+\
                "Inactive Time,Rest Time,Low Activity Time,"+\
                "Medium Activity Time,High Activity Time,Non-wear Time,"+\
                "Average MET,Long Periods of Inactivity,Readiness Score,"+\
                "Previous Night Score,Sleep Balance Score,"+\
                "Previous Day Activity Score,Activity Balance Score,"+\
                "Temperature Score,Resting Heart Rate Score,"+\
                "HRV Balance Score,Recovery Index Score").split(",")
        return None

    def build_day(self, df_row):
        if self == DataSource.toggl:
            d = df_row["Start date"].split("-")
            # TODO needs to specify accumulator function
            d = Day(year=int(d[0]), month=int(d[1]), day=int(d[2]))
            d.add_record(str(self), dict(
                Texts=" ".join([df_row[k] for k in [
                    "Project", "Task", "Tags", "Description"
                ] if type(df_row[k]) == str]),
                **{k:df_row[k] for k in self.get_fields()})
                )
            return d
        elif self == DataSource.oura:
            d = df_row["date"].split("-")
            d = Day(year=int(d[0]), month=int(d[1]), day=int(d[2]))
            d.update({"%s_%s"%(self, k):df_row[k] for k in self.get_fields()})
            return d
        assert False

    def __str__(self):
        return self.value

    def get_help(self):

        intro_msg = lambda is_optional, src: "%s data from --%s."%(
            "Accepts" if is_optional else "Requires", src
        )

        h = ""

        if self == DataSource.eventlog:
            h += "\n%s\n"%intro_msg(is_optional=False, src="data")
            h += "\n%s\n"%intro_msg(is_optional=True, src="meta")

        elif self == DataSource.worklog:
            h += "\n%s\n"%(intro_msg(is_optional=False, src="data"))
            h += textwrap.dedent('''\
                     All data is specified manually in a JSON. The data lists exceptions: date and a number,
                     between 0 and 1, indicating proportion of workday. Otherwise, it is assumed that
                     non-working-days and regional holidays are off; and the rest of the days have 8-hour
                     work days. Should specify start and end dates, and holiday region (optional).

                     --data worklog.json
                       {
                        "comments": " very difficult work time, last-minute project push.",
                        "first_day": "2020-11-30",
                        "last_day": "2020-12-23",
                        "working_days": "MTWRF",
                        "working_hours": 8,
                        "exceptions": {
                            "2020-12-4": 0,
                            "2020-12-17": 0,
                            "2020-12-18": 0
                        }

                     Possible output:
                     * Exception is irrelevant (3 warnings, which are listed in -v mode)
                     * Total number of days in thetime span, proportion of working days
                     * Total number of workhours logged
                     ''')
        return h

    @staticmethod
    def all_help():
        return "\n\n".join(["%s\n%s\n%s\n%s"%("-"*80, v, "-"*80, v.get_help()) for v in list(DataSource)])
