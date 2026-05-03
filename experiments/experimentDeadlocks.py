from db.database import DB
from services import serviceDeadlocks as deadlocks
from config.settings import WORKLOAD, ITERATIONS

def cleanup(db):
    db.deleteschema()
    db.initialize()

def start():
    #for i in range(ITERATIONS):
    for j in range(WORKLOAD):
        data = deadlocks.main()
        print(data)


def main():
    db = DB()
    cleanup(db)
    start()

if __name__ == "__main__":
    main()