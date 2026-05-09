from asyncio import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from time import sleep

from db.database import DB
from config.settings import ITERATIONS, WORKLOAD, RETRY_STRATEGY, CONCURRENCY, RETRY_COUNT, RETRY_DELAY
from core.coreDeadlocks import *

def _get_params(rc, rd, rs, wl, it, cc):
    retry_count = RETRY_COUNT[rc]
    retry_delay = RETRY_DELAY[rd]
    retry_strategy = RETRY_STRATEGY[rs]
    workload = WORKLOAD[wl]
    concurrency = CONCURRENCY[cc]
    run_key = f"s:{retry_strategy}_r{retry_count}_d{retry_delay}_w{workload}_i{it}_cc{concurrency}"

    return run_key, retry_count, retry_delay, retry_strategy, workload, concurrency

def _clear_database():
    db = DB()
    db.delete_schema()
    db.initialize()
    db.close()

def _soft_reset_database():
    db = DB()
    db.rollback_all()
    sleep(2)
    db.close()

def _log_event(path, record):
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")

def _create_log(run_id, strategy, count, delay, workload, iterations, concurrency):
    record = {"type": "run_meta", "run_id": run_id, "strategy": strategy, "retry_count": count,
              "retry_delay": delay, "workload": workload, "iterations": iterations, "concurrency": concurrency,
              "timestamp": time.time()}

    path = BASE_DIR + LOG_PATH

    _log_event(path, record)

def _client(client_id, iteration, run_id, strategy, count, delay):
    db = DB()

    match strategy:
        case "no_retry":
            run_without_retry(client_id, db, iteration, run_id)
        case "no_delay":
            run_without_delay(client_id, db, iteration, run_id, count)
        case "static_delay":
            run_with_static_delay(client_id, db, iteration, run_id, count, delay)
        case "exponential_delay":
            run_with_exponential_delay(client_id, db, iteration, run_id, count, delay)
        case "jitter_delay":
            run_retry_with_jitter_delay(client_id, db, iteration, run_id, count, delay)

    db.close()

def _run_batch(rk, rs, rc, rd, wl, it, cc):
    with ThreadPoolExecutor(max_workers=cc,) as executor:
        futures = []
        print("Iteration:", it)
        for l in range(wl):
            executor.submit(_client, l, it, rk, rs, rc, rd)

        for f in as_completed(futures):
            f.result()


def _experiment_0(it):
    rc_idx = 0
    rd_idx = 0
    rs_idx = 0

    for i in range(len(CONCURRENCY)):
        for j in range(len(WORKLOAD)):
            rk, rc, rd, rs, wl, cc = _get_params(rc_idx, rd_idx, rs_idx, j, it, i)
            print("")
            print("Concurrency:", cc)
            print("Workload:", wl)
            _create_log(rk, rs, rc, rd, wl, it, cc)
            _run_batch(rk, rs, rc, rd, wl, it, cc)


def start_deadlocks():
    _clear_database()
    start = time.perf_counter()
    for h in range(ITERATIONS):
        _experiment_0(h)


    end = time.perf_counter()
    print(start - end, "s")
