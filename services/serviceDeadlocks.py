def tx_a(db):
    cur = db.conn.cursor()
    cur.execute("SELECT salary FROM deadlocks WHERE id = 1 FOR UPDATE;")
    cur.execute("UPDATE deadlocks SET salary = 100 WHERE id = 2;")


def tx_b(db):
    cur = db.conn.cursor()
    cur.execute("SELECT salary FROM deadlocks WHERE id = 2 FOR UPDATE;")
    cur.execute("UPDATE deadlocks SET salary = 200 WHERE id = 1;")

def run_transaction(client_id, db):
    if client_id % 2 == 0:
        tx_a(db)
    else:
        tx_b(db)