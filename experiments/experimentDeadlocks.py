from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep

from db.database import DB
from config.settings import ITERATIONS, WORKLOAD, RETRY_STRATEGY, CONCURRENCY, RETRY_COUNT, RETRY_DELAY
from core.coreDeadlocks import *

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

def _get_params(rc, rd, rs, wl, it, cc):
    retry_count = RETRY_COUNT[rc]
    retry_delay = RETRY_DELAY[rd]
    retry_strategy = RETRY_STRATEGY[rs]
    workload = WORKLOAD[wl]
    concurrency = CONCURRENCY[cc]
    run_key = f"s{retry_strategy}_r{retry_count}_d{retry_delay}_w{workload}_i{it}_cc{concurrency}"

    return run_key, retry_count, retry_delay, retry_strategy, workload, concurrency

def _client(client_id, iteration, run_id, strategy, count, delay):
    db = DB()
    result = 0

    match strategy:
        case 0:
            result = run_without_retry(client_id, db, iteration, run_id)
        case 1:
            result = run_without_delay(client_id, db, iteration, run_id, count)
        case 2:
            result = run_with_static_delay(client_id, db, iteration, run_id, count, delay)
        case 3:
            result = run_retry_with_jitter_delay(client_id, db, iteration, run_id, count, delay)

    db.close()

    return result

def _run_batch(rk, rs, rc, rd, wl, it, cc):
    path = BASE_DIR + LOG_PATH
    with ThreadPoolExecutor(max_workers=cc,) as executor:
        futures = []
        print("Iteration(batch):", it)
        for l in range(wl):
            futures.append(executor.submit(_client, l, it, rk, rs, rc, rd))

        for f in as_completed(futures):
            record = f.result()

            if ENABLE_LOGGING:
                _log_event(path, record)

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

    for cc_idx in range(len(CONCURRENCY)):
        if cc_idx == 0 or cc_idx == 4:
            rk, rc, rd, rs, wl, cc = _get_params(rc_idx, rd_idx, rs_idx, wl_idx, 0, cc_idx)
            rk = "WARM-UP"
            _run_batch(rk, rs, rc, rd, wl, 0, cc)

def _experiment_0(it):
    rc_idx = 0
    rd_idx = 0
    rs_idx = 0

    for cc_idx in range(len(CONCURRENCY)):
        #if cc_idx in [0, 2, 4]:
            print("CC_Index:", cc_idx)
            for wl_idx in range(len(WORKLOAD)):
                _start_experiment(rc_idx, rd_idx, rs_idx, it, cc_idx, wl_idx)

def _experiment_1(it):
    rd_idx = 0
    rs_idx = 1

    for cc_idx in range(len(CONCURRENCY)):
        if cc_idx in [0, 2, 4]:
            for wl_idx in range(len(WORKLOAD)):
                for rc_idx in range(len(RETRY_COUNT)):
                    if rc_idx == 1 or rc_idx == 2:
                        _start_experiment(rc_idx, rd_idx, rs_idx, it, cc_idx, wl_idx)

def _experiment_2(it):
    rc_idx = 3
    rd_idx = 0
    rs_idx = 1
    cc_idx = 4
    wl_idx = 1

    _start_experiment(rc_idx, rd_idx, rs_idx, it, cc_idx, wl_idx)

def _experiment_3(it):
    rc_idx = 2
    rs_idx = 2

    for cc_idx in range(len(CONCURRENCY)):
        if cc_idx == 2 or cc_idx == 4:
            for wl_idx in range(len(WORKLOAD)):
                for rd_idx in range(len(RETRY_DELAY)):
                    _start_experiment(rc_idx, rd_idx, rs_idx, it, cc_idx, wl_idx)

def _experiment_4(it):
    rc_idx = 3
    cc_idx = 4
    wl_idx = 1

    for rd_idx in range(len(RETRY_DELAY)):
        if rd_idx in [1, 2]:
            for rs_idx in range(len(RETRY_STRATEGY)):
                if rs_idx in [2, 3]:
                    _start_experiment(rc_idx, rd_idx, rs_idx, it, cc_idx, wl_idx)

def _experiment_5(it):
    wl_idx = 1

    for cc_idx in range(len(CONCURRENCY)):
        if cc_idx != 2:
            for rc_idx in range(len(RETRY_COUNT)):
                if rc_idx in [0, 2]:
                    for rd_idx in range(len(RETRY_DELAY) - 1):
                        for rs_idx in range(len(RETRY_STRATEGY)):
                            if rs_idx in [2, 3]:
                                _start_experiment(rc_idx, rd_idx, rs_idx, it, cc_idx, wl_idx)


def start_deadlocks():
    #_clear_database()
    #_warmup_database()
    start = time.perf_counter()
    for it in range(ITERATIONS):
        print("Iteration:", it)
        #_experiment_0(it)
        #_experiment_1(it)
        #_experiment_2(it)
        _experiment_3(it)
        #_experiment_4(it)
        #_experiment_5(it)

        _soft_reset_database()

    end = time.perf_counter()
    print(end - start, "s")
