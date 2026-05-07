import test
from experiments.experimentDeadlocks import start_deadlocks
from db.database import DB

def _clear_database(db):
    db.delete_schema()
    db.initialize()
    db.close()

def main():
    db = DB()
    _clear_database(db)
    #test.test_function()
    start_deadlocks()

if __name__ == "__main__":
    main()
