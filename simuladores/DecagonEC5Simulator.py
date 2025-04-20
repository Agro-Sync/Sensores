import os
import random
import math
from datetime import datetime
import pandas as pd
from pymysql import Error
import psutil


class DecagonEC5Simulator:
    """
    Simulador do sensor de Umidade do Solo com capacidade de:
    - Simulação realista de umidade do solo
    - Geração de DataFrame com os dados
    - Armazenamento no MySQL na tabela FatoValores
    """

    def __init__(self, sensor_id=None, region_id=None, mysql_connector=None):
        self.max_moisture = 100
        self.calibration_factor = 1.0
        self.sensor_id = sensor_id
        self.region_id = region_id
        self.mysql_connector = mysql_connector

    def calibrate(self, calibration_factor=1.0):
        self.calibration_factor = calibration_factor
        print(f"Sensor calibrado com fator {calibration_factor:.2f}")

    def simulate_moisture(self, base_value=None):
        if base_value is None:
            now = datetime.now()
            hour = now.hour + now.minute / 60 + now.second / 3600

            # Simulação com evaporação durante o dia (menor umidade ao meio-dia)
            base_value = 60 - 20 * math.sin(math.pi * (hour - 6) / 12)
            base_value = max(0, min(base_value, self.max_moisture))
        else:
            base_value = min(max(base_value, 0), self.max_moisture)

        noise = random.gauss(0, base_value * 0.02 + 2)
        max_variation = base_value * 0.02 + 2
        measured_value = base_value + max(-max_variation, min(noise, max_variation))
        calibrated_value = measured_value * self.calibration_factor
        return min(max(round(calibrated_value, 1), 0), self.max_moisture)

    def _save_to_mysql(self, data_frame, num_sample):
        if not all([self.mysql_connector, self.sensor_id is not None, self.region_id is not None]):
            print("Configuração MySQL incompleta - pulando salvamento no banco")
            return False

        try:
            with self.mysql_connector.get_connection() as conn:
                with conn.cursor() as cursor:
                    values = []
                    cpu_usage = psutil.cpu_percent()

                    process = psutil.Process(os.getpid())
                    mem_bytes = process.memory_info().rss
                    mem_mb = mem_bytes / (1024 * 1024)

                    for _, row in data_frame.iterrows():
                        time_init = row['timestamp']
                        values.append((
                            self.sensor_id,
                            row['umidade'],
                            time_init.strftime('%Y-%m-%d'),
                            time_init,
                            datetime.now(),
                            num_sample,
                            mem_mb,
                            cpu_usage,
                            'DecagonEC5',
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
            'umidade': []
        }

        try:
            for _ in range(num_samples):
                timestamp = datetime.now()
                umidade = self.simulate_moisture()

                data['timestamp'].append(timestamp)
                data['umidade'].append(umidade)

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

    sensor = DecagonEC5Simulator(
        sensor_id=2,
        region_id=1,
        mysql_connector=mysql_connector
    )

    df = sensor.collect_data(
        num_samples=15,
        save_to_db=True
    )

    print("\nEstatísticas dos dados coletados:")
    print(df.describe())
