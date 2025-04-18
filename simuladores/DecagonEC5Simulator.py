import random
import math
from datetime import datetime
import pandas as pd
from pymysql import Error


class SoilMoistureSimulator:
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

    @staticmethod
    def _get_time_id(timestamp):
        return int(timestamp.strftime("%Y%m%d%H"))

    def _save_to_mysql(self, data_frame):
        if not all([self.mysql_connector, self.sensor_id is not None, self.region_id is not None]):
            print("Configuração MySQL incompleta - pulando salvamento no banco")
            return False

        try:
            with self.mysql_connector.get_connection() as conn:
                with conn.cursor() as cursor:
                    for _, row in data_frame.iterrows():
                        time_id = self._get_time_id(row['timestamp'])

                        cursor.execute("SELECT IFNULL(MAX(idValor), 0) + 1 FROM agrosync.FatoValores")
                        next_id = cursor.fetchone()[0]

                        cursor.execute(
                            "INSERT INTO agrosync.FatoValores (idValor, idSensor, idRegiao, idTempo, Valor) "
                            "VALUES (%s, %s, %s, %s, %s)",
                            (next_id, self.sensor_id, self.region_id, time_id, row['moisture'])
                        )

                    conn.commit()
                    print(f"Dados salvos no MySQL. Total: {len(data_frame)} registros")
                    return True

        except Error as e:
            print(f"Erro ao salvar no MySQL: {e}")
            return False

    def collect_data(self, num_samples, save_to_db=False):
        data = {
            'timestamp': [],
            'moisture': []
        }

        try:
            for _ in range(num_samples):
                timestamp = datetime.now()
                moisture = self.simulate_moisture()

                data['timestamp'].append(timestamp)
                data['moisture'].append(moisture)

        except KeyboardInterrupt:
            print("\nColeta interrompida pelo usuário")
        finally:
            df = pd.DataFrame(data)

            if save_to_db:
                self._save_to_mysql(df)

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

    sensor = SoilMoistureSimulator(
        sensor_id=2,  # Exemplo: sensor_id diferente para umidade
        region_id=1,
        mysql_connector=mysql_connector
    )

    df = sensor.collect_data(
        num_samples=15,
        save_to_db=False
    )

    print("\nEstatísticas dos dados coletados:")
    print(df.describe())
