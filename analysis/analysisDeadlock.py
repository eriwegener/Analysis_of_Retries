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

def _retry_distribution(data):
    df = data.copy()
    df_success = df[df["status"] == "success"]
    df_success["r"] = df_success["run_id"].str.extract(r"_(r\d+)_")
    result = df_success.groupby("r").size().sort_index()

    result.index = "r" + result.index
    result.index.name = None

    print("\n=== retry-distribution ===")
    print(result)

def _latency_comparison(data):
    df = data.copy()
    df_success = df[df["status"] == "success"]
    df_success["s"] = df_success["run_id"].str.extract(r"(s\d+)_")

    success = df_success.groupby("s").size().sort_index()
    success.index.name = None

    avg = (df_success.groupby("s")["total_ms"].mean())
    avg.index.name = None

    #print(success)
    print(avg)

def _quartiles(data):
    df = data.copy()
    df_success = df[df["status"] == "success"]
    df_success["s"] = df_success["run_id"].str.extract(r"(s\d+)_")

    df_failed = df[df["status"] == "failed"]
    df_failed["f"] = df_failed["run_id"].str.extract(r"(s\d+)_")

    quantiles_success = df_success["total_ms"].quantile([0.50, 0.95, 0.99])
    quantiles_failed = df_failed["total_ms"].quantile([0.50, 0.95, 0.99])

    print(quantiles_success)
    print("")
    print(quantiles_failed)

def _retry_overhead(data):
    df_overhead = data.copy()

    df_overhead["s"] = df_overhead["run_id"].str.extract(r"(s\d+)_")
    df_overhead["cc"] = df_overhead["run_id"].str.extract(r"_(cc\d+)")
    df_overhead["count"] = df_overhead["run_id"].str.extract(r"_(r\d+)_")

    df_overhead["attempts_trimmed"] = (df_overhead["attempts_ms"].
                                       apply(lambda x: x[1:] if isinstance(x, list) and len(x) > 1 else []))
    df_overhead["best_ms"] = (df_overhead["attempts_trimmed"].
                                      apply(lambda x: min(x) if len(x) > 0 else 0))
    df_overhead["overhead"] = df_overhead["total_ms"] - df_overhead["best_ms"]

    s_avg = df_overhead.groupby(["s", "status"])["overhead"].mean()
    cc_avg = df_overhead.groupby(["cc", "status"])["overhead"].mean()
    rc_avg = df_overhead.groupby(["count", "status"])["overhead"].mean()

    print("=== strategy ===")
    print(s_avg)

    print("")
    print("=== concurrency ===")
    print(cc_avg)

    print("")
    print("=== retry count ===")
    print(rc_avg)

def start_analysis():
    data = _get_data()

    #_success_rates(data)
    print("")
    #_retry_distribution(data)
    #_latency_comparison(data)
    #_quartiles(data)
    #_retry_overhead(data)
