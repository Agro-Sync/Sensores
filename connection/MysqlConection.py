import pymysql
from pymysql import Error
from contextlib import contextmanager

class MySQLConnector:
    def __init__(self, host, database, user, password, **kwargs):
        self.connection_params = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
            **kwargs
        }
    
    @contextmanager
    def get_connection(self):
        """
        Fornece uma conexão gerenciada por contexto
        Uso:
        with mysql_connector.get_connection() as conn:
            # operações com a conexão
        """
        conn = None
        try:
            conn = pymysql.connect(**self.connection_params)
            yield conn
        except Error as e:
            print(f"Erro MySQL: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query, params=None, fetch=False):
        """
        Executa uma query de forma segura
        Retorna:
        - Para SELECT com fetch=True: lista de resultados
        - Para outras queries: número de linhas afetadas
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if fetch:
                    result = cursor.fetchall()
                else:
                    result = cursor.rowcount
                conn.commit()
                return result
    
    def get_next_id(self, table, id_column='id'):
        """
        Obtém o próximo ID disponível para uma tabela
        """
        query = f"SELECT IFNULL(MAX({id_column}), 0) + 1 AS next_id FROM {table}"
        result = self.execute_query(query, fetch=True)
        return result[0]['next_id'] if result else 1