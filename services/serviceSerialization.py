from time import sleep

def _tx_a(db):
    cur = db.conn.cursor()
    cur.execute("SELECT amount FROM serialization WHERE id = 1;")
    sleep(0.05)
    cur.execute("UPDATE serialization SET amount = amount + 1 WHERE id = 1;")


def _tx_b(db):
    cur = db.conn.cursor()
    cur.execute("SELECT amount FROM serialization WHERE id = 1;")
    sleep(0.05)
    cur.execute("UPDATE serialization SET amount = amount + 1 WHERE id = 1;")

def run_transaction_serialization(client_id, db):
    if client_id % 2 == 0:
        _tx_a(db)
    else:
        _tx_b(db)