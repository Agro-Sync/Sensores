import random
from datetime import datetime
import pandas as pd
from pymysql import Error
import psutil
import os

class Davis6410Simulator:
    """
    Simulador do sensor Anemômetro Davis 6410:
    - Simula velocidade e direção do vento
    - Geração de DataFrame com os dados
    - Armazenamento no MySQL na tabela FatoValores
    """

    def __init__(self, sensor_id=None, region_id=None, mysql_connector=None):
        self.sensor_id = sensor_id
        self.region_id = region_id
        self.mysql_connector = mysql_connector

    def simulate_wind_speed(self):
        """
        Simula a velocidade do vento em m/s, com base em distribuição normal truncada.
        """
        base_speed = random.gauss(5, 2)  
        base_speed = max(0, min(base_speed, 30))  
        return round(base_speed, 2)

    def simulate_wind_direction(self, prev_direction=None):
        """
        Simula a direção do vento em graus (0 a 360), com variação gradual.
        """
        if prev_direction is None:
            return round(random.uniform(0, 360), 2)
        variation = random.gauss(0, 10)  
        new_direction = (prev_direction + variation) % 360
        return round(new_direction, 2)

    def _save_to_mysql(self, data_frame, num_sample):
        if not all([self.mysql_connector, self.sensor_id is not None, self.region_id is not None]):
            print("Configuração MySQL incompleta - pulando salvamento no banco")
            return False

        try:
            with self.mysql_connector.get_connection() as conn:
                with conn.cursor() as cursor:
                    values = []
                    cpu_usage = psutil.cpu_percent()
                    mem_bytes = psutil.Process(os.getpid()).memory_info().rss
                    mem_mb = mem_bytes / (1024 * 1024)

                    for _, row in data_frame.iterrows():
                        values.append((
                            self.sensor_id,
                            row['wind_speed'],  
                            row['timestamp'].strftime('%Y-%m-%d'),
                            row['timestamp'],
                            datetime.now(),
                            num_sample,
                            mem_mb,
                            cpu_usage,
                            'Davis6410'
                        ))
                    self._execute_batch_insert(cursor, values)
                    conn.commit()
        except Error as e:
            print(f"Erro ao salvar no MySQL: {e}")
            return False

    @staticmethod
    def _execute_batch_insert(cursor, values):
        query = """
        INSERT INTO agrosync.log_exec 
        (id_sensor, valor, dt_exec, dt_start_exec, dt_end_exec, qtd_data, ram_usage, process_usage, sensor_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(query, values)

    def collect_data(self, num_samples, save_to_db=False):
        data = {
            'timestamp': [],
            'wind_speed': [],
            'wind_direction': []
        }

        prev_direction = None

        try:
            for _ in range(num_samples):
                timestamp = datetime.now()
                speed = self.simulate_wind_speed()
                direction = self.simulate_wind_direction(prev_direction)
                prev_direction = direction

                data['timestamp'].append(timestamp)
                data['wind_speed'].append(speed)
                data['wind_direction'].append(direction)

        except KeyboardInterrupt:
            print("\nColeta interrompida pelo usuário")
        finally:
            df = pd.DataFrame(data)
            if save_to_db:
                self._save_to_mysql(df, num_samples)
            return df

if __name__ == "__main__":
    from connection import MySQLConnector  

    mysql_config = {
        'host': 'localhost',
        'database': 'agrosync',
        'user': 'seu_usuario',
        'password': 'sua_senha'
    }

    mysql_connector = MySQLConnector(**mysql_config)

    sensor = Davis6410Simulator(
        sensor_id=2,
        region_id=1,
        mysql_connector=mysql_connector
    )

    df = sensor.collect_data(
        num_samples=20,
        save_to_db=True
    )

    print("\nEstatísticas dos dados coletados:")
    print(df.describe())
