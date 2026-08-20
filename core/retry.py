import math
import random
import psycopg2.errors
import time

from services.serviceDeadlocks import run_transaction_deadlocks
from services.serviceSerialization import run_transaction_serialization
from services.serviceTimeout import run_transaction_timeouts


def _start_transaction(client_id, db, caller_name):
    start = time.perf_counter()
    res = 0
    pgcode = 00000
    try:
        if caller_name == "start_deadlocks":
            db.begin()
            run_transaction_deadlocks(client_id, db)
            db.commit()
            res = "success"
        elif caller_name == "start_serialization":
            db.begin()
            db.isolation()
            run_transaction_serialization(client_id, db)
            db.commit()
            res = "success"
        elif caller_name == "start_timeout":
            db.begin()
            db.lock_timeout()
            run_transaction_timeouts(client_id, db)
            db.commit()
            res = "success"
    except psycopg2.Error as e:
        res = "failed"
        pgcode = e.pgcode

    duration_ms = math.floor((time.perf_counter() - start) * 1000)

    return res, duration_ms, pgcode

def run_retry_with_jitter_delay(client_id, db, iteration, run_id, retry_count, retry_delay, caller_name):
    retries = 0
    attempt_times = []

    start = time.perf_counter()
    data, duration_ms, pgcode = _start_transaction(client_id, db, caller_name)
    attempt_times.append(duration_ms)

    while data == "failed" and retries < retry_count:
        db.rollback()
        delay = random.uniform(0, retry_delay * (2 ** retries))
        time.sleep(delay)

        data, duration_ms, pgcode = _start_transaction(client_id, db, caller_name)
        attempt_times.append(duration_ms)
        retries += 1

    finish = time.perf_counter()
    total_ms = math.floor((finish - start) * 1000)

    return {"type": "tx_event", "run_id": run_id, "iteration": iteration, "retries": retries,
            "attempts_ms": attempt_times, "total_ms": total_ms, "status": data, "pg_code": pgcode, "tx_start": start,
            "tx_finish": finish}

def run_with_static_delay(client_id, db, iteration, run_id, retry_count, retry_delay, caller_name):
    retries = 0
    attempt_times = []

    start = time.perf_counter()
    data, duration_ms, pgcode = _start_transaction(client_id, db, caller_name)
    attempt_times.append(duration_ms)

    while data == "failed" and retries < retry_count:
        db.rollback()
        delay = retry_delay
        time.sleep(delay)

        data, duration_ms, pgcode = _start_transaction(client_id, db, caller_name)
        attempt_times.append(duration_ms)
        retries += 1

    finish = time.perf_counter()
    total_ms = math.floor((finish - start) * 1000)

    return {"type": "tx_event", "run_id": run_id, "iteration": iteration, "retries": retries,
            "attempts_ms": attempt_times, "total_ms": total_ms, "status": data, "pg_code": pgcode, "tx_start": start,
            "tx_finish": finish}

def run_without_delay(client_id, db, iteration, run_id, retry_count, caller_name):
    retries = 0
    attempt_times = []

    start = time.perf_counter()
    data, duration_ms, pgcode = _start_transaction(client_id, db, caller_name)
    attempt_times.append(duration_ms)

    while data == "failed" and retries < retry_count:
        db.rollback()
        delay = 0
        time.sleep(delay)

        data, duration_ms, pgcode = _start_transaction(client_id, db, caller_name)
        attempt_times.append(duration_ms)
        retries += 1

    finish = time.perf_counter()
    total_ms = math.floor((finish - start) * 1000)

    return {"type": "tx_event", "run_id": run_id, "iteration": iteration, "retries": retries,
            "attempts_ms": attempt_times, "total_ms": total_ms, "status": data, "pg_code": pgcode, "tx_start": start,
            "tx_finish": finish}

def run_without_retry(client_id, db, iteration, run_id, caller_name):
    retries = None
    attempt_times = []

    start = time.perf_counter()
    data, duration_ms, pgcode = _start_transaction(client_id, db, caller_name)
    attempt_times.append(duration_ms)

    finish = time.perf_counter()
    total_ms = math.floor((finish - start) * 1000)

    return {"type": "tx_event", "run_id": run_id, "iteration": iteration, "retries": retries,
     "attempts_ms": attempt_times, "total_ms": total_ms, "status": data, "pg_code": pgcode, "tx_start": start,
     "tx_finish": finish}
