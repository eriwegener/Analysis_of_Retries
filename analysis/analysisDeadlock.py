#Success-Rate
#Retry-Distribution
#Latency-Comparison
#Quartils
#Retry-Overhead
#Throughput
#Influence of Workload
#Influence of Delay
#Failures despite Retry
#Stability over Duration

import pandas as pd

from config.settings import LOG_PATH, BASE_DIR, WORKLOAD, ITERATIONS

def _get_data():
    path = BASE_DIR + LOG_PATH
    with open(path, "r") as f:
        df = pd.read_json(f, lines=True)

    return df.iloc[4000:]

def _success_rates(data):
    df = data.copy()
    concurrency = data.copy()
    strategy = data.copy()
    retry = data.copy()

    concurrency["cc"] = concurrency["run_id"].str.extract(r"_(cc\d+)")
    strategy["s"] = strategy["run_id"].str.extract(r"(s\d+)_")
    retry["r"] = retry["run_id"].str.extract(r"_(r\d+)_")

    cc_counts = concurrency.groupby(["cc", "status"]).size().unstack(fill_value=0)
    cc_rates = cc_counts.div(cc_counts.sum(axis=1), axis=0) * 100
    cc_rates.index.name = None

    s_counts = strategy.groupby(["s", "status"]).size().unstack(fill_value=0)
    s_rates = s_counts.div(s_counts.sum(axis=1), axis=0) * 100
    s_rates.index.name = None

    r_counts = retry.groupby(["r", "status"]).size().unstack(fill_value=0)
    r_rates = r_counts.div(r_counts.sum(axis=1), axis=0) * 100
    r_rates.index.name = None

    total_counts = df["status"].value_counts()
    total_rate = (total_counts / total_counts.sum()) * 100

    print("")
    print("=== concurrency ===")
    print(cc_rates)

    print("")
    print("=== strategy ===")
    print(s_rates)

    print("")
    print("=== retry ===")
    print(r_rates)

    print("")
    print("\n=== total ===")
    print(total_rate)

#def _retry_Distribution():


def start_analysis():
    data = _get_data()

    _success_rates(data)
