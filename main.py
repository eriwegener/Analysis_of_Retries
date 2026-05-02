from db.database import DB
import deadlocks

def testQuery():
    db = DB()
    data = db.query("Select * From deadlocks limit 1")
    print("Data from Database:", data)

def main():
    testQuery()
    deadlocks.greet()

if __name__ == "__main__":
    main()
