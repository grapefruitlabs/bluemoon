import json
import argparse
import sys

from .models import Dataset, Day, AllData
from .data_sources import DataSource
from . import get_aggregate_data


def bmdb_add_data(db_target, data_source, data, description):

    all_data = AllData.build(db_target)

    # First build the dataset without overwriting
    ds = data_source.build_dataset(data, base_dataset=all_data.dataset)
    ds.set_ready(True)

    n_updates = all_data.update(ds, description=description)

    all_data.set_serializable_field(str(data_source))
    with open(db_target, 'w', encoding='utf-8') as f:
        json.dump(all_data.as_dict(), f, ensure_ascii=False, indent=4)
    return n_updates


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
          formatter_class=argparse.RawDescriptionHelpFormatter,
          epilog=DataSource.all_help())

    parser.add_argument('db_target', type=str, help="Please specify a valid filename; if nonexistent, will be created.")
    parser.add_argument('--data_source', type=DataSource, choices=list(DataSource), help="Please use of one the available data source types.")
    parser.add_argument('--data', '-d', type=str, help="Must conform to expected data source data formatting")
    parser.add_argument('--meta', '-m', type=str, help="Must conform to expected data source meta formatting")
    parser.add_argument('--silent', '-s', action='store_true', default=False,
        help="Flag that optionally turns off changelog saves")

    opts = parser.parse_args()
    n_updates = bmdb_add_data(
        db_target=opts.db_target,
        data_source=opts.data_source,
        data=opts.data,
        description=".add %s"%" ".join(sys.argv[1:]) if not opts.silent else None
    )
    print("Registered", n_updates, "updates")
