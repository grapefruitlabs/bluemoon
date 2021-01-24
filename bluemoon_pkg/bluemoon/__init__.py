import glob
import pandas as pd

def get_aggregate_data(path):
    """
    path: Expected to be either a file or set of files,
          eg. "../../dirname/*.csv"
    return pandas DataFrame
    """

    result = None
    for datafile in glob.glob(path):
        if result is None:
            result = pd.read_csv(datafile)
        else:
            result = result.append(pd.read_csv(datafile))
    return result
