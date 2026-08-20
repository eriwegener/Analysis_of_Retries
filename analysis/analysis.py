import pandas as pd
from scipy import stats

from config.settings import LOG_PATH_E, BASE_DIR, ENABLE_TEST

def _get_data(path):
    if ENABLE_TEST:
        path = BASE_DIR + LOG_PATH_E
    with open(path, "r") as f:
        df = pd.read_json(f, lines=True)

    if ENABLE_TEST:
        return df
    else:
        df = df[df["type"] == "tx_event"]
        df = df[~df["run_id"].str.startswith("WARM-UP")]

        hdf = df[~df["pg_code"].isin([0, "40P01", 40001, "55P03"])]
        if len(hdf):
            print(len(hdf), "errors, coming from other sources.")
            print(hdf["pg_code"])

        return df

def _print(value, title, param, pstatus):
    print(f"=== {param} {title} {pstatus} ===")
    print(value.to_string())
    print("")

def _sort_numeric(data):
    return data.sort_index(
        level=[0, 1],
        key=lambda x: x.str.extract(r"([\d.]+)")[0].astype(float) if hasattr(x, 'str') else x
    )

def _evaluate_metric_with_stats(data, metric_col="total_ms", param=None, pstatus=None):
    df = data.copy()

    df["it"] = df["run_id"].str.extract(r"(i\d+)")
    if param:
        df[param] = df["run_id"].str.extract(fr"({param}[\d.]+)")

    if pstatus:
        df = df[df["status"] == pstatus]

    group_cols_it = [param, "status", "it"] if param else ["status", "it"]
    df_it = df.groupby(group_cols_it)[metric_col].mean().reset_index()

    def _calc_ci95(series):
        n = len(series)
        if n < 2:
            return 0.0
        return stats.sem(series) * stats.t.ppf((1 + 0.95) / 2., n - 1)

    agg_cols = [param, "status"] if param else ["status"]

    result = df_it.groupby(agg_cols)[metric_col].agg(
        mean="mean",
        std="std",
        count="count",
        ci95=_calc_ci95
    ).reset_index()

    print(result)

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
        result = df.groupby([param, "retries", "status"], dropna=False).size().unstack(fill_value=0)
    else:
        result = df.groupby(["retries", "status"], dropna=False).size().unstack(fill_value=0)

    if pstatus == "success":
        result = result["success"]
    elif pstatus == "failed":
        result = result["failed"]

    result = _sort_numeric(result)

    _print(result, "retry-distribution", param, pstatus)

def _execution_comparison(data, param, pstatus):
    df = data.copy()

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

    _print(result, "execution_comparison", "", "")

def _quantiles(data, param, pstatus):
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

    _print(quantiles, "quantiles", param, pstatus)

def _retry_overhead(data, param, pstatus):
    df = data.copy()

    df["e"] = df["run_id"].str.extract(fr"(e[1-9]\d*)")
    df[param] = df["run_id"].str.extract(fr"({param}[\d.]+)")

    df["overhead"] = df.apply(
        lambda row: row["total_ms"] - row["attempts_ms"][0]
        if isinstance(row["attempts_ms"], list) and len(row["attempts_ms"]) > 1
        else 0,
        axis=1
    )

    if param:
        result = df.groupby([param, "status"])["overhead"].mean().unstack(fill_value=0)
    else:
        result = df.groupby(["status"])["overhead"].mean()

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
    _execution_comparison(data, "cc", "")
    _quantiles(data, "cc", "")
    _retry_overhead(data, "cc", "")
    _throughput(data, "cc")

def _influence_delay(data):
    print("=== influence-delay ===")
    _rates(data, "d", "")
    _retry_distribution(data, "d", "")
    _execution_comparison(data, "d", "")
    _quantiles(data, "d", "")
    _retry_overhead(data, "d", "")
    _throughput(data, "d")

def _influence_retry(data):
    print("=== influence-retry ===")
    _rates(data, "r", "")
    _retry_distribution(data, "r", "")
    _execution_comparison(data, "r", "")
    _quantiles(data, "r", "")
    _retry_overhead(data, "r", "")
    _throughput(data, "r")

def _influence_strategy(data):
    print("=== influence-strategy ===")
    _rates(data, "s", "")
    _retry_distribution(data, "s", "")
    _execution_comparison(data, "s", "")
    _quantiles(data, "s", "")
    _retry_overhead(data, "s", "")
    _throughput(data, "s")

def _overall(data):
    print("=== overall ===")
    _rates(data, "", "")
    _retry_distribution(data, "", "")
    _execution_comparison(data, "", "")
    _quantiles(data, "", "")
    _retry_overhead(data, "", "")
    _throughput(data, "")

def start_analysis(path):
    data = _get_data(path)

    _evaluate_metric_with_stats(data)
    _overall(data)
    _influence_concurrency(data)
    _influence_delay(data)
    _influence_retry(data)
    _influence_strategy(data)