import pymysql
from pymysql import Error

class MySQLConnector:
    
    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
    
    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return True
        except Error as e:
            print(f"Erro ao conectar ao MySQL: {e}")
            return False
    
    def disconnect(self):
        if self.connection and self.connection.open:
            self.connection.close()
    
    def execute_query(self, query, params=None, fetch=False):
        if not self.connection or not self.connection.open:
            if not self.connect():
                return None
                
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                if fetch:
                    result = cursor.fetchall()
                else:
                    result = cursor.rowcount
                self.connection.commit()
                return result
        except Error as e:
            print(f"Erro ao executar query: {e}")
            self.connection.rollback()
            return None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()