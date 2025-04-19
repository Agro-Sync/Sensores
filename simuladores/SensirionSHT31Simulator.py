from datetime import datetime
from pymysql import Error
import pandas as pd
import random
import psutil

class SHT31Simulator:
    """
    Simulador do sensor Sensirion SHT31 com capacidade de:
    - Simulação realista de humidade relativa do ar
    - Geração de DataFrame com os dados
    - Armazenamento no MySQL na tabela FatoValores
    """

    def __init__(self, sensor_id=None, region_id=None, mysql_connector=None):
        self.max_humidity = 100
        self.calibration_factor = 1.0
        self.sensor_id = sensor_id
        self.region_id = region_id
        self.mysql_connector = mysql_connector

    def calibrate(self, calibration_factor=1.0):
        self.calibration_factor = calibration_factor
        print(f"Sensor calibrado com fator {calibration_factor:.2f}")

    def simulate_humidity(self, base_value=None):
        if base_value is None:
            now = datetime.now()
            hour = now.hour + now.minute / 60 + now.second / 3600

            if 5 <= hour <= 19:
                base_value = random.uniform(40, 100)
            else:
                base_value = random.uniform(0, 40)

        noise = random.gauss(0, base_value * 0.02 + 2)
        max_variation = base_value * 0.05 + 5
        measured_value = base_value + max(-max_variation, min(noise, max_variation))
        calibrated_value = measured_value * self.calibration_factor
        return min(max(round(calibrated_value, 1), 0), self.max_humidity)

    def _save_to_mysql(self, data_frame, num_sample):
        if not all([self.mysql_connector, self.sensor_id is not None, self.region_id is not None]):
            print("Configuração MySQL incompleta - pulando salvamento no banco")
            return False

        try:
            with self.mysql_connector.get_connection() as conn:
                with conn.cursor() as cursor:
                    values = []
                    cpu_usage = psutil.cpu_percent()

                    for _, row in data_frame.iterrows():
                        time_init = row['timestamp']
                        values.append((
                            self.sensor_id,
                            row['humidity'],
                            time_init.strftime('%Y-%m-%d'),
                            time_init,
                            datetime.now(),
                            num_sample,
                            cpu_usage,
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
        (id_sensor, valor, dt_exec, dt_start_exec, dt_end_exec, qtd_data, process_usage)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(query, values)

    def collect_data(self, num_samples, save_to_db=False):
        data = {
            'timestamp': [],
            'humidity': []
        }

        try:
            for _ in range(num_samples):
                timestamp = datetime.now()
                humidity = self.simulate_humidity()

                data['timestamp'].append(timestamp)
                data['humidity'].append(humidity)

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
        'user': 'root',
        'password': 'urubu100'
    }
    mysql_connector = MySQLConnector(**mysql_config)

    sensor = SHT31Simulator(
        sensor_id=1,
        region_id=1,
        mysql_connector=mysql_connector
    )

    df = sensor.collect_data(
        num_samples=15,
        save_to_db=True
    )

    print("\nEstatísticas dos dados coletados:")
    print(df.describe())