# bluemoon
"A blue moon is an additional full moon that appears in a subdivision of a year: either the third of four full moons in a season, or a second full moon in a month of the common calendar."

## Set-up

1. Navigate to the root directory.
2. Install the package: `pip install -e bluemoon_pkg/` in editable mode
3. Verify that the unit tests pass: `py.test`
4. Verify that the integration tests pass: `python -m bluemoon.test bluemoon_pkg/bluemoon_tests/data` - should either print `ALL CLEAR!` or specify which tests failed. Note that you can run this command in `--verbose` or `-v` mode to help debug.
5. Set up a blank bluemoon database by running `python -m bluemoon.add NAME_OF_DB.json`

## Adding Data

Check out what data formats and integrations are supported: `python -m bluemoon.add --help`
Note that everything marked with a "*" is an integration, while others are local data formats.

For example, to add Toggl data:

`python -m bluemoon.add mydata.json --data_source *toggl --data data/B_toggl/*.csv`

And to add a worklog:

`python -m bluemoon.add mydata.json --data_source worklog --data data/worklog.json`

where the worklog might look like this:

```
{
 "comments": "A very difficult work time, last-minute project push.",
 "first_day": "2020-11-30",
 "last_day": "2020-12-23",
 "working_days": "MTWRF",
 "working_hours": 8,
 "exceptions": {
     "2020-12-4": 0,
     "2020-12-17": 2,
     "2020-12-18": 3
 }
```

### Supported Integrations Notes

* Exist.io: requires token for bearer auth, which can be found using `curl https://exist.io/api/1/auth/simple-token/ -d username=... -d password=...`
* Toggl: requires the detailed csv export
* Fitbit: requires the csv export; supporting "Sleep" and "Activity"
* Oura: requires the csv export
* Last.fm: requires downloading all scrobble events as a csv [eg, with this](https://benjaminbenben.com/lastfm-to-csv/)

## Core Concepts

1. **Day** is the primary unit of analysis, and each day has a different measure of data availability relative to an analysis, depending on surrounding days' data
2. **Reports** for experiments and insights are not separated from data, but are themselves data and usable in analysis
3. **Implicit** data is added: (1) scheduled work and (2) habits that don't need to be tracked, which may have fuzzy day boundaries
4. **Exceptional** days are identified based on cluster analysis, using most representative and available data dimensions

## Changelog

* 0.1.1 - First tests added
