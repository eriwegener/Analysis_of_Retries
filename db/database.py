import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class DB:
    def __init__(self):
        self.conn = psycopg2.connect(dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
                                     password=os.getenv("DB_PASSWORD"), host=os.getenv("DB_HOST"))

    def query(self, sql):
        cursor = self.conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()

        return result

    def close(self):
        self.conn.close()