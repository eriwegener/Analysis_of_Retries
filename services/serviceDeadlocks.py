from time import sleep


def _tx_a(db):
    cur = db.conn.cursor()
    cur.execute("SELECT salary FROM deadlocks WHERE id = 1 FOR UPDATE;")
    sleep(0.05)
    cur.execute("UPDATE deadlocks SET salary = 100 WHERE id = 2;")


def _tx_b(db):
    cur = db.conn.cursor()
    cur.execute("SELECT salary FROM deadlocks WHERE id = 2 FOR UPDATE;")
    sleep(0.05)
    cur.execute("UPDATE deadlocks SET salary = 200 WHERE id = 1;")

def run_transaction(client_id, db):
    if client_id % 2 == 0:
        _tx_a(db)
    else:
        _tx_b(db)