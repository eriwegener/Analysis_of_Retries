import threading
from threading import Barrier
from db.database import DB

def tx_a(db, barrier):
    cur = db.conn.cursor()
    cur.execute("BEGIN;")
    cur.execute("SELECT salary FROM deadlocks WHERE id = 1 FOR UPDATE;")

    barrier.wait()

    cur.execute("UPDATE deadlocks SET salary = 100 WHERE id = 2;")
    db.conn.commit()


def tx_b(db, barrier):
    cur = db.conn.cursor()
    cur.execute("BEGIN;")
    cur.execute("SELECT salary FROM deadlocks WHERE id = 2 FOR UPDATE;")

    barrier.wait()

    cur.execute("UPDATE deadlocks SET salary = 200 WHERE id = 1;")
    db.conn.commit()


def main():
    db1 = DB()
    db2 = DB()
    barrier = Barrier(2)
    t1 = threading.Thread(target=tx_a, args=(db1, barrier))
    t2 = threading.Thread(target=tx_b, args=(db2, barrier))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

if __name__ == "__main__":
    main()