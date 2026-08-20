from time import sleep

def _tx_a(db):
    cur = db.conn.cursor()
    cur.execute("SELECT amount FROM timeouts WHERE id = 1 FOR UPDATE;")
    sleep(1)

def _tx_b(db):
    cur = db.conn.cursor()
    cur.execute("SELECT amount FROM timeouts WHERE id = 1 FOR UPDATE;")
    sleep(1)

def run_transaction_timeouts(client_id, db):
    if client_id % 2 == 0:
        _tx_a(db)
    else:
        _tx_b(db)