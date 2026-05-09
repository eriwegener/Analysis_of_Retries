import math
import random
import psycopg2.errors
import time
import json

from services.serviceDeadlocks import run_transaction
from config.settings import LOG_PATH, ENABLE_LOGGING, BASE_DIR

def _log_event(path, record):
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")

def _create_log(run_id, iteration, retries, attempt_times, total_ms, status, start, finish):
    record = {"type": "tx_event", "run_id": run_id, "iteration": iteration, "retries": retries,
              "attempts_ms": attempt_times, "total_ms": total_ms, "status": status, "tx_start": start,
              "tx_finish": finish}

    path = BASE_DIR + LOG_PATH

    _log_event(path, record)

def _start_transaction(client_id, db):
    start = time.perf_counter()
    try:
        db.begin()
        run_transaction(client_id, db)
        db.commit()
        res = "success"
    except psycopg2.errors.DeadlockDetected:
        res = "failed"

    duration_ms = math.floor((time.perf_counter() - start) * 1000)

    return res, duration_ms

def run_retry_with_jitter_delay(client_id, db, iteration, run_id, retry_count, retry_delay):
    retries = 0
    attempt_times = []

    start = time.perf_counter()
    data, duration_ms = _start_transaction(client_id, db)
    attempt_times.append(duration_ms)

    while data == "failed" and retries < retry_count:
        db.rollback()
        delay = random.uniform(0, retry_delay[2] * (2 ** retries))
        time.sleep(delay)

        data, duration_ms = _start_transaction(client_id, db)
        attempt_times.append(duration_ms)
        retries += 1

    finish = time.perf_counter()
    total_ms = math.floor((finish - start) * 1000)

    if ENABLE_LOGGING:
        _create_log(run_id, iteration, retries, attempt_times, total_ms, data, start, finish)

def run_with_exponential_delay(client_id, db, iteration, run_id, retry_count, retry_delay):
    retries = 0
    attempt_times = []

    start = time.perf_counter()
    data, duration_ms = _start_transaction(client_id, db)
    attempt_times.append(duration_ms)

    while data == "failed" and retries < retry_count:
        db.rollback()
        delay = retry_delay * (2 ** retries)
        time.sleep(delay)

        data, duration_ms = _start_transaction(client_id, db)
        attempt_times.append(duration_ms)
        retries += 1

    finish = time.perf_counter()
    total_ms = math.floor((finish - start) * 1000)

    if ENABLE_LOGGING:
        _create_log(run_id, iteration, retries, attempt_times, total_ms, data, start, finish)

def run_with_static_delay(client_id, db, iteration, run_id, retry_count, retry_delay):
    retries = 0
    attempt_times = []

    start = time.perf_counter()
    data, duration_ms = _start_transaction(client_id, db)
    attempt_times.append(duration_ms)

    while data == "failed" and retries < retry_count:
        db.rollback()
        delay = retry_delay
        time.sleep(delay)

        data, duration_ms = _start_transaction(client_id, db)
        attempt_times.append(duration_ms)
        retries += 1

    finish = time.perf_counter()
    total_ms = math.floor((finish - start) * 1000)

    if ENABLE_LOGGING:
        _create_log(run_id, iteration, retries, attempt_times, total_ms, data, start, finish)

def run_without_delay(client_id, db, iteration, run_id, retry_count):
    retries = 0
    attempt_times = []

    start = time.perf_counter()
    data, duration_ms = _start_transaction(client_id, db)
    attempt_times.append(duration_ms)

    while data == "failed" and retries < retry_count:
        db.rollback()
        delay = 0
        time.sleep(delay)

        data, duration_ms = _start_transaction(client_id, db)
        attempt_times.append(duration_ms)
        retries += 1

    finish = time.perf_counter()
    total_ms = math.floor((finish - start) * 1000)

    if ENABLE_LOGGING:
        _create_log(run_id, iteration, retries, attempt_times, total_ms, data, start, finish)

def run_without_retry(client_id, db, iteration, run_id):
    retries = None
    attempt_times = []

    start = time.perf_counter()
    data, duration_ms = _start_transaction(client_id, db)
    attempt_times.append(duration_ms)

    finish = time.perf_counter()
    total_ms = math.floor((finish - start) * 1000)

    if ENABLE_LOGGING:
        _create_log(run_id, iteration, retries, attempt_times, total_ms, data, start, finish)
