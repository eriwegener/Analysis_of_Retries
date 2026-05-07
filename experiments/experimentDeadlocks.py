import threading
from db.database import DB
from config.settings import ITERATIONS, WORKLOAD, RETRY_ENABLED
from core.coreDeadlocks import *

def _client(client_id, iteration):
    db = DB()

    if RETRY_ENABLED:
        run_with_retry(client_id, db, iteration)
    else:
        run_without_retry(client_id, db, iteration)

    db.close()


def start_deadlocks():
    threads = []

    for k in range(ITERATIONS):
        print(k)
        for i in range(WORKLOAD):
            t = threading.Thread(target=_client, args=(i, k,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()