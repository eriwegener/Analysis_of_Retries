import math

import psycopg2.errors
import time

from services.serviceDeadlocks import run_transaction

def start_transaction(client_id, db):
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

def run_with_retry(client_id, db):

    data, duration_ms = start_transaction(client_id, db)

    print(client_id, data)
    while data == "failed":
        db.rollback()
        data, duration_ms = start_transaction(client_id, db)
        print(client_id, data)

    print(duration_ms, "ms + client_id:", client_id)