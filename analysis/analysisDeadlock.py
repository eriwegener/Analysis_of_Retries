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

    return df

def _success_rate(data):
    df = data.copy()
    df["cc"] = df["run_id"].str.extract(r"_(cc\d+)")

    counts = df.groupby(["cc", "status"]).size().unstack(fill_value=0)
    rates = counts.div(counts.sum(axis=1), axis=0) * 100
    rates.index.name = None

    total_counts = df["status"].value_counts()
    total_rate = (total_counts / total_counts.sum()) * 100

    print("=== cc ===")
    print(rates)

    print("\n=== total ===")
    print(total_rate)

#def _retry_Distribution():


def start_analysis():
    data = _get_data()

    _success_rate(data)
