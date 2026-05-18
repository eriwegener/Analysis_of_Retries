import pandas as pd

from config.settings import LOG_PATH, BASE_DIR, ENABLE_TEST

def _get_data():
    path = BASE_DIR + LOG_PATH
    with open(path, "r") as f:
        df = pd.read_json(f, lines=True)

    if ENABLE_TEST:
        return df
    else:
        return df.iloc[1000:]

def _print(value, title, param, pstatus):
    print(f"=== {param} {title} {pstatus} ===")
    print(value.to_string())
    print("")

def _sort_numeric(data):
    return data.sort_index(
        level=[0, 1],
        key=lambda x: x.str.extract(r"([\d.]+)")[0].astype(float) if hasattr(x, 'str') else x
    )

def _rates(data, param, pstatus):
    df = data.copy()

    if param:
        df[param] = df["run_id"].str.extract(fr"({param}[\d.]+)")
        counts = df.groupby([param, "status"]).size().unstack(fill_value=0)
        rates = counts.div(counts.sum(axis=1), axis=0) * 100

    else:
        counts = df.groupby(["status"]).size()
        rates = counts.div(counts.sum()) * 100

    if pstatus == "success":
        rates = rates["success"]
    elif pstatus == "failed":
        rates = rates["failed"]

    rates = _sort_numeric(rates)

    _print(rates, "rates", param, pstatus)

def _retry_distribution(data, param, pstatus):
    df = data.copy()
    df[param] = df["run_id"].str.extract(fr"({param}[\d.]+)")

    if param:
        result = df.groupby([param, "retries", "status"]).size().unstack(fill_value=0)
    else:
        result = df.groupby(["retries", "status"]).size().unstack(fill_value=0)

    if pstatus == "success":
        result = result["success"]
    elif pstatus == "failed":
        result = result["failed"]

    result = _sort_numeric(result)

    _print(result, "retry-distribution", param, pstatus)

def _latency_comparison(data, param, pstatus):
    df = data.copy()
    df["e"] = df["run_id"].str.extract(r"(e\d+)_")

    if param:
        df[param] = df["run_id"].str.extract(fr"({param}[\d.]+)")
        result = (df.groupby([param, "status"])["total_ms"].mean().unstack(fill_value=0))
    else:
        result = (df.groupby(["status"])["total_ms"].mean())

    if pstatus == "success":
        result = result["success"]
    elif pstatus == "failed":
        result = result["failed"]

    result = _sort_numeric(result)

    _print(result, "latency_comparison", "", "")

def _quartiles(data, param, pstatus):
    df = data.copy()
    if param:
        df[param] = df["run_id"].str.extract(fr"({param}[\d.]+)")
        quantiles = df.groupby([param, "status",])["total_ms"].quantile([0.50, 0.95, 0.99, 0.999]).unstack(fill_value=0)
    else:
        quantiles = df.groupby("status")["total_ms"].quantile([0.50, 0.95, 0.99, 0.999]).unstack(fill_value=0)

    if pstatus == "success":
        quantiles = quantiles["success"]
    elif pstatus == "failed":
        quantiles = quantiles["failed"]

    quantiles = _sort_numeric(quantiles)

    _print(quantiles, "quartiles", param, pstatus)

def _retry_overhead(data, param, pstatus):
    df_overhead = data.copy()

    df_overhead["e"] = df_overhead["run_id"].str.extract(fr"(e[\d.]+)")
    df_overhead[param] = df_overhead["run_id"].str.extract(fr"({param}[\d.]+)")

    df_overhead["attempts_trimmed"] = (df_overhead["attempts_ms"].
                                       apply(lambda x: x[1:] if isinstance(x, list) and len(x) > 1 else []))
    df_overhead["best_ms"] = (df_overhead["attempts_trimmed"].
                                      apply(lambda x: min(x) if len(x) > 0 else 0))
    df_overhead["overhead"] = df_overhead["total_ms"] - df_overhead["best_ms"]

    if param:
        result = df_overhead.groupby([param, "status"])["overhead"].mean().unstack(fill_value=0)
    else:
        result = df_overhead.groupby(["status"])["overhead"].mean()

    if pstatus == "success":
        result = result["success"]
    elif pstatus == "failed":
        result = result["failed"]

    result = _sort_numeric(result)

    _print(result, "retry-overhead", param, pstatus)

def _throughput(data, param):
    df = data.copy()

    df["e"] = df["run_id"].str.extract(r"(e\d+)_")
    df_time = df.groupby(["e"]).agg(start_time=("tx_start", "min"), end_time=("tx_finish", "max"))
    if param:
        df[param] = df["run_id"].str.extract(fr"({param}[\d.]+)")

        df_success = df[df["status"] == "success"].groupby(["e", param]).agg(successful_retries=("run_id", "count"))
    else:
        df_success = df[df["status"] == "success"].groupby(["e"]).agg(successful_retries=("run_id", "count"))

    df_time["duration"] = df_time["end_time"] - df_time["start_time"]

    result = df_time.join(df_success, how="left").fillna(0)
    result["throughput"] = result["successful_retries"] / result["duration"]

    result = _sort_numeric(result)

    _print(result[["successful_retries", "duration", "throughput"]], "throughput", "", "")

def _influence_concurrency(data):
    print("=== influence-concurrency ===")
    _rates(data, "cc", "")
    _retry_distribution(data, "cc", "")
    _latency_comparison(data, "cc", "")
    _quartiles(data, "cc", "")
    _retry_overhead(data, "cc", "")
    _throughput(data, "cc")

def _influence_delay(data):
    print("=== influence-delay ===")
    _rates(data, "d", "")
    _retry_distribution(data, "d", "")
    _latency_comparison(data, "d", "")
    _quartiles(data, "d", "")
    _retry_overhead(data, "d", "")
    _throughput(data, "d")

def _influence_retry(data):
    print("=== influence-retry ===")
    _rates(data, "r", "")
    _retry_distribution(data, "r", "")
    _latency_comparison(data, "r", "")
    _quartiles(data, "r", "")
    _retry_overhead(data, "r", "")
    _throughput(data, "r")

def _influence_strategy(data):
    print("=== influence-strategy ===")
    _rates(data, "s", "")
    _retry_distribution(data, "s", "")
    _latency_comparison(data, "s", "")
    _quartiles(data, "s", "")
    _retry_overhead(data, "s", "")
    _throughput(data, "s")

def _overall(data):
    print("=== overall ===")
    _rates(data, "", "")
    _retry_distribution(data, "", "")
    _latency_comparison(data, "", "")
    _quartiles(data, "", "")
    _retry_overhead(data, "", "")
    _throughput(data, "")

def start_analysis():
    data = _get_data()

    _overall(data)
    _influence_concurrency(data)
    _influence_delay(data)
    _influence_retry(data)
    _influence_strategy(data)
