from db.database import DB
from services import serviceDeadlocks as deadlocks
from config.settings import WORKLOAD, ITERATIONS

def cleanup(db):
    db.deleteschema()
    db.initialize()

def start():
    db1 = DB()
    db2 = DB()
    barrier = Barrier(2)
    t1 = threading.Thread(target=tx_a, args=(db1, barrier))
    t2 = threading.Thread(target=tx_b, args=(db2, barrier))
    t1.start()
    t2.start()
    t1.join()
    t2.join()


def main():
    db = DB()
    cleanup(db)
    start()

if __name__ == "__main__":
    main()