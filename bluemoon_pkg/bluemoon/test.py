# Integration test suite

import json
import argparse

from . import get_aggregate_data
from .data_sources import DataSource
from .models import AllData
from .add import bmdb_add_data

def test_get_aggregate_data(path_to_test_data):
    result = get_aggregate_data("%s/toggl*.csv"%path_to_test_data)
    assert (10, 14) == result.shape

def test_bmdb_add_data_toggl(path_to_test_data):

    db_target = "%s/test-sdb.json"%path_to_test_data
    # empty the file
    with open(db_target, 'w', encoding='utf-8') as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

    # Read in data
    result = bmdb_add_data(
        db_target=db_target,
        data_source=DataSource.toggl,
        data="%s/toggl*.csv"%path_to_test_data,
        description="test")
    assert 4 == result # Only 4 days when the rows are accumulated
    all_data = AllData.build(db_target)

    n_rows = all_data.dataset.count_cumulative_entries(str(DataSource.toggl))
    assert 10 == n_rows # all the rows are stored in accumulated field

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('path_to_test_data', type=str,
        help="Path to the /storyteller_tests/data folder")
    parser.add_argument('--verbose', '-v', action='store_true', default=False,
        help="Flag that optionally turns on verbose mode")
    opts = parser.parse_args()

    # Test top-level utils
    test_get_aggregate_data(opts.path_to_test_data)
    test_bmdb_add_data_toggl(opts.path_to_test_data)

    print("ALL CLEAR!")
