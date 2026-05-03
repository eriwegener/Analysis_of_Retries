import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class DB:
    def __init__(self):
        self.conn = psycopg2.connect(dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
                                     password=os.getenv("DB_PASSWORD"), host=os.getenv("DB_HOST"))
        self.conn.autocommit = False

    def query(self, sql):
        cursor = self.conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()

        return result

    def deleteschema(self):
        cursor = self.conn.cursor()
        cursor.execute("DROP SCHEMA public CASCADE")
        cursor.execute("COMMIT")
        cursor.close()

    def initialize(self):
        cursor = self.conn.cursor()
        cursor.execute("CREATE SCHEMA public")
        cursor.execute("CREATE TABLE deadlocks(id SERIAL, salary INT)")
        for i in range(5):
            cursor.execute("INSERT INTO deadlocks(salary) VALUES (%s)", ((i + 1) * 100,))

        cursor.execute("COMMIT")
        cursor.close()

    def begin(self):
        cursor = self.conn.cursor()
        cursor.execute("BEGIN;")
        cursor.close()

    def commit(self):
        cursor = self.conn.cursor()
        cursor.execute("COMMIT")
        cursor.close()

    def rollback(self):
        cursor = self.conn.cursor()
        cursor.execute("ROLLBACK")
        cursor.close()

    def close(self):
        self.conn.close()