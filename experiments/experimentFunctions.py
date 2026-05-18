import json
import inspect

from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep
from db.database import DB
from config.settings import WORKLOAD, RETRY_STRATEGY, CONCURRENCY, RETRY_COUNT, RETRY_DELAY, ENABLE_TEST, \
    ENABLE_LOGGING, BASE_DIR, LOG_PATH, ITERATIONS
from core.retry import *

def _log_event(path, record):
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")

def _create_log(run_id, strategy, count, delay, workload, iterations, concurrency):
    record = {"type": "run_meta", "run_id": run_id, "strategy": strategy, "retry_count": count,
              "retry_delay": delay, "workload": workload, "iterations": iterations, "concurrency": concurrency,
              "timestamp": time.time()}

    path = BASE_DIR + LOG_PATH

    _log_event(path, record)

def _get_params(rc, rd, rs, wl, it, cc):
    retry_count = RETRY_COUNT[rc]
    retry_delay = RETRY_DELAY[rd]
    retry_strategy = RETRY_STRATEGY[rs]
    workload = WORKLOAD[wl]
    concurrency = CONCURRENCY[cc]
    run_key = f"s{retry_strategy}_r{retry_count}_d{retry_delay}_w{workload}_i{it}_cc{concurrency}"

    return run_key, retry_count, retry_delay, retry_strategy, workload, concurrency

def _client(client_id, iteration, run_id, strategy, count, delay, caller_name):
    db = DB()
    result = 0

    match strategy:
        case 0:
            result = run_without_retry(client_id, db, iteration, run_id, caller_name)
        case 1:
            result = run_without_delay(client_id, db, iteration, run_id, count, caller_name)
        case 2:
            result = run_with_static_delay(client_id, db, iteration, run_id, count, delay, caller_name)
        case 3:
            result = run_retry_with_jitter_delay(client_id, db, iteration, run_id, count, delay, caller_name)

    db.close()

    return result

def _run_batch(rk, rs, rc, rd, wl, it, cc):
    path = BASE_DIR + LOG_PATH

    if rk == "WARM-UP":
        caller_frame = inspect.stack()[3][0]
    else:
        caller_frame = inspect.stack()[4][0]
    caller_name = caller_frame.f_code.co_name

    with ThreadPoolExecutor(max_workers=cc,) as executor:
        futures = []
        print("Iteration(batch):", it)
        for l in range(wl):
            futures.append(executor.submit(_client, l, it, rk, rs, rc, rd, caller_name))

        for f in as_completed(futures):
            record = f.result()
            if ENABLE_LOGGING:
                _log_event(path, record)

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

def _start_experiment(rc_idx, rd_idx, rs_idx, it, cc_idx, wl_idx):
    rk, rc, rd, rs, wl, cc = _get_params(rc_idx, rd_idx, rs_idx, wl_idx, it, cc_idx)
    if ENABLE_LOGGING:
        _create_log(rk, rs, rc, rd, wl, it, cc)
    _run_batch(rk, rs, rc, rd, wl, it, cc)

def _warmup_database():
    rc_idx = 0
    rd_idx = 0
    rs_idx = 0
    wl_idx = 0
    it = 0

    if ENABLE_TEST:
        for cc_idx in range(3, len(CONCURRENCY)):
            rk, rc, rd, rs, wl, cc = _get_params(rc_idx, rd_idx, rs_idx, wl_idx, it, cc_idx)
            rk = "WARM-UP"
            _run_batch(rk, rs, rc, rd, wl, it, cc)

def _experiment_0(): #Baseline
    rc_idx = 0
    rd_idx = 0
    rs_idx = 0
    wl_idx = 0

    if ENABLE_TEST:
        for cc_idx in range(len(CONCURRENCY)): #5
            print("CC_Index:", cc_idx)
            _start_experiment(rc_idx, rd_idx, rs_idx, 0, cc_idx, wl_idx)
    else:
        for it in range(ITERATIONS):
            for cc_idx in range(len(CONCURRENCY)): #25
                _start_experiment(rc_idx, rd_idx, rs_idx, it, cc_idx, wl_idx)

def _experiment_1(): #Retry without Delay
    rd_idx = 0
    rs_idx = 1
    wl_idx = 0
    valid_combinations = [
        (rc, cc)
        for rc in range(1, len(RETRY_COUNT))
        for cc in range(len(CONCURRENCY))
    ]

    if ENABLE_TEST:
        for rc_idx, cc_idx in valid_combinations: #15
            print("CC_Index:", cc_idx)
            _start_experiment(rc_idx, rd_idx, rs_idx, 0, cc_idx, wl_idx)
    else:
        for it in range(ITERATIONS):
            for rc_idx, cc_idx in valid_combinations: #75
                _start_experiment(rc_idx, rd_idx, rs_idx, it, cc_idx, wl_idx)
            _soft_reset_database()

def _experiment_2(): #Delay
    rc_idx = 2
    rs_idx = 2
    wl_idx = 0
    valid_combinations = [
        (rd, cc)
        for rd in range(1, len(RETRY_DELAY))
        for cc in range(len(CONCURRENCY))
    ]

    if ENABLE_TEST:
        for rd_idx, cc_idx in valid_combinations: #20
            print("CC_Index:", cc_idx)
            _start_experiment(rc_idx, rd_idx, rs_idx, 0, cc_idx, wl_idx)
    else:
        for it in range(ITERATIONS):
            for rd_idx, cc_idx in valid_combinations: #100
                _start_experiment(rc_idx, rd_idx, rs_idx, it, cc_idx, wl_idx)
            _soft_reset_database()

def _experiment_3(): #Strategy
    rd_idx = 2
    wl_idx = 0
    valid_combinations = [
        (rs, rc, cc)
        for rs in range(2, len(RETRY_STRATEGY))
        for rc in range(1, len(RETRY_COUNT))
        for cc in range(len(CONCURRENCY))
        if rs != 2 or rc != 2
    ]

    if ENABLE_TEST:
        for rs_idx, rc_idx, cc_idx in valid_combinations: #25
            print("CC_IDX: ", cc_idx)
            _start_experiment(rc_idx, rd_idx, rs_idx, 0, cc_idx, wl_idx)
    else:
        for it in range(ITERATIONS):
            for rs_idx , rc_idx, cc_idx in valid_combinations: #125
                _start_experiment(rc_idx, rd_idx, rs_idx, it, cc_idx, wl_idx)
            _soft_reset_database()

def start():
    _clear_database()
    _warmup_database()
    t_start = time.perf_counter()

    print("=== Experiment0 ===")
    _experiment_0()
    print("=== Experiment1 ===")
    _experiment_1()
    print("=== Experiment2 ===")
    _experiment_2()
    print("=== Experiment3 ===")
    _experiment_3()

    t_end = time.perf_counter()
    print(t_end - t_start, "s")