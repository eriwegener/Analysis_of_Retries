import threading
from db.database import DB
from config.settings import ITERATIONS, WORKLOAD
from core.coreDeadlocks import run_with_retry

def client(client_id, results):
    db = DB()

    for _ in range(ITERATIONS):
        data = run_with_retry(client_id, db)

        results.append(data)

def start_deadlocks():
    threads = []
    results = []

    for i in range(WORKLOAD):
        t = threading.Thread(target=client, args=(i, results))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return results