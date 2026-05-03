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


if __name__ == "__main__":
    main()