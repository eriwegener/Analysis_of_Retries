#Stability over Duration

import pandas as pd

from config.settings import LOG_PATH, BASE_DIR

def _get_data():
    path = BASE_DIR + LOG_PATH
    with open(path, "r") as f:
        df = pd.read_json(f, lines=True)

    return df.iloc[4000:]

def _print(value, title, pstatus):
    print(f"=== {title} {pstatus} ===")
    print(value.to_string())
    print("")

def _rates(data, param, pstatus):
    df = data.copy()

    df["s"] = df["run_id"].str.extract(r"(s\d+)_")
    df[param] = df["run_id"].str.extract(fr"({param}\d+)")

    if param:
        counts = df.groupby([param, "status"]).size().unstack(fill_value=0)
        rates = counts.div(counts.sum(axis=1), axis=0) * 100

        if pstatus == "success":
            rates = rates["success"]
        elif pstatus == "failed":
            rates = rates["failed"]
    else:
        counts = df.groupby(["s", "status"]).size().unstack(fill_value=0)
        rates = counts.div(counts.sum(axis=1), axis=0) * 100

        if pstatus == "success":
            rates = rates["success"]
        elif pstatus == "failed":
            rates = rates["failed"]

    _print(rates, "rates", pstatus)

def _retry_distribution(data, param, pstatus):
    df = data.copy()
    df["r"] = df["run_id"].str.extract(r"_(r\d+)_")
    df[param] = df["run_id"].str.extract(fr"({param}\d+)")
    if param:
        result = df.groupby(["r", param, "status"]).size().unstack(fill_value=0)
    else:
        result = df.groupby(["r", "status"]).size().unstack(fill_value=0)

    if pstatus == "success":
        result = result["success"]
    elif pstatus == "failed":
        result = result["failed"]

    _print(result, "retry-distribution", pstatus)

def _latency_comparison(data, pstatus):
    df = data.copy()
    df["s"] = df["run_id"].str.extract(r"(s\d+)_")
    result = (df.groupby(["s", "status"])["total_ms"].mean().unstack(fill_value=0))

    if pstatus == "success":
        result = result["success"]
    elif pstatus == "failed":
        result = result["failed"]

    _print(result, "latency_comparison", "")

def _quartiles(data, param, pstatus):
    df = data.copy()
    if param:
        df[param] = df["run_id"].str.extract(fr"({param}\d+)")
        quantiles = df.groupby([param, "status",])["total_ms"].quantile([0.50, 0.95, 0.99]).unstack(fill_value=0)
    else:
        quantiles = df.groupby("status")["total_ms"].quantile([0.50, 0.95, 0.99]).unstack(fill_value=0)

    if pstatus == "success":
        quantiles = quantiles["success"]
    elif pstatus == "failed":
        quantiles = quantiles["failed"]

    _print(quantiles, "quartiles", pstatus)

def _retry_overhead(data, param, pstatus):
    df_overhead = data.copy()

    df_overhead[param] = df_overhead["run_id"].str.extract(fr"({param}\d+)")

    df_overhead["attempts_trimmed"] = (df_overhead["attempts_ms"].
                                       apply(lambda x: x[1:] if isinstance(x, list) and len(x) > 1 else []))
    df_overhead["best_ms"] = (df_overhead["attempts_trimmed"].
                                      apply(lambda x: min(x) if len(x) > 0 else 0))
    df_overhead["overhead"] = df_overhead["total_ms"] - df_overhead["best_ms"]

    result = df_overhead.groupby([param, "status"])["overhead"].mean().unstack(fill_value=0)

    if pstatus == "success":
        result = result["success"]
    elif pstatus == "failed":
        result = result["failed"]

    _print(result, "retry-overhead", pstatus)

def _throughput(data, param):
    df = data.copy()

    df["s"] = df["run_id"].str.extract(r"(s\d+)_")
    df_time = df.groupby(["s"]).agg(start_time=("tx_start", "min"), end_time=("tx_finish", "max"))
    if param:
        df[param] = df["run_id"].str.extract(fr"({param}\d+)")

        df_success = df[df["status"] == "success"].groupby(["s", param]).agg(successful_retries=("run_id", "count"))
    else:
        df_success = df[df["status"] == "success"].groupby(["s"]).agg(successful_retries=("run_id", "count"))

    df_time["duration"] = df_time["end_time"] - df_time["start_time"]

    system = df_time.join(df_success, how="left").fillna(0)
    system["throughput"] = system["successful_retries"] / system["duration"]

    _print(system[["successful_retries", "duration", "throughput"]], "throughput", "")

def _influence_workload(data):
    print("=== influence-workload ===")
    _rates(data, "w", "")
    _throughput(data, "w")
    _quartiles(data, "w", "")

def _influence_delay(data):
    print("=== influence-delay ===")
    _rates(data, "d", "")
    _retry_distribution(data, "d", "")
    _throughput(data, "d")
    _quartiles(data, "d", "")

def _failure_retry(data):
    df = data.copy()

    retries_count = df.groupby(["retries", "status"]).size().unstack(fill_value=0)
    retries_count = retries_count["failed"]

    print("=== failure-retry ===")
    _rates(data, "cc", "failed")
    _rates(data, "", "failed")
    _print(retries_count, "retry_count", "failed")

def start_analysis():
    data = _get_data()

    _rates(data, "", "")
    _retry_distribution(data, "", "")
    _latency_comparison(data, "")
    _quartiles(data, "s", "")
    _retry_overhead(data, "cc", "")
    _throughput(data, "")
    _influence_workload(data)
    _influence_delay(data)
    _failure_retry(data)
