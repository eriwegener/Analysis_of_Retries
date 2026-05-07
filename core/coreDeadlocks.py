import math
import random
import psycopg2.errors
import time
import json

from services.serviceDeadlocks import run_transaction
from config.settings import RETRY_COUNT, RETRY_DELAY, LOG_PATH

def _log_event(path, record):
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")

def _create_log(client_id, iteration, retries, attempt_times, total_ms, data):
    record = {"client_id": client_id, "iteration": iteration, "retries": retries, "attempts_ms": attempt_times, "total_ms": total_ms,
              "status": data, "timestamp": time.time()}

    _log_event(LOG_PATH, record)

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

def run_with_retry(client_id, db, iteration):
    retries = 0
    attempt_times = []

    start = time.perf_counter()
    data, duration_ms = _start_transaction(client_id, db)
    attempt_times.append(duration_ms)

    while data == "failed" and retries < RETRY_COUNT:
        db.rollback()
        delay = random.uniform(0, RETRY_DELAY * (2 ** retries))
        time.sleep(delay)

        data, duration_ms = _start_transaction(client_id, db)
        attempt_times.append(duration_ms)
        retries += 1

    total_ms = math.floor((time.perf_counter() - start) * 1000)

    _create_log(client_id, iteration, retries, attempt_times, total_ms, data)


def run_without_retry(client_id, db, iteration):
    retries = "NULL"
    attempt_times = []

    start = time.perf_counter()
    data, duration_ms = _start_transaction(client_id, db)
    attempt_times.append(duration_ms)

    total_ms = math.floor((time.perf_counter() - start) * 1000)

    _create_log(client_id, iteration, retries, attempt_times, total_ms, data)
