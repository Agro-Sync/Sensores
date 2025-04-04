import random
import math
from datetime import datetime
import pandas as pd
from pymysql import Error


class ApogeeSP110Simulator:
    """
    Simulador do sensor Apogee SP-110 com capacidade de:
    - Simulação realista de irradiância solar
    - Geração de DataFrame com os dados
    - Armazenamento no MySQL na tabela FatoValores
    """

    def __init__(self, sensor_id=None, region_id=None, mysql_connector=None):
        self.max_irradiance = 2000
        self.calibration_factor = 1.0
        self.sensor_id = sensor_id
        self.region_id = region_id
        self.mysql_connector = mysql_connector

    def calibrate(self, calibration_factor=1.0):
        self.calibration_factor = calibration_factor
        print(f"Sensor calibrado com fator {calibration_factor:.2f}")

    def simulate_irradiance(self, base_value=None):
        if base_value is None:
            now = datetime.now()
            hour = now.hour + now.minute / 60 + now.second / 3600

            if 5 <= hour <= 19:
                solar_angle = math.pi * (hour - 12) / 15
                max_irradiance = 1000
                base_value = max_irradiance * math.sin(math.pi / 2 - abs(solar_angle)) ** 1.5
                base_value = max(0, base_value)

                if hour < 6 or hour > 18:
                    base_value *= 0.3 * (1 - abs(hour - 12) / 6)
            else:
                base_value = random.uniform(0, 10)
        else:
            base_value = min(max(base_value, 0), self.max_irradiance)

        noise = random.gauss(0, base_value * 0.02 + 2)
        max_variation = base_value * 0.05 + 5
        measured_value = base_value + max(-max_variation, min(noise, max_variation))
        calibrated_value = measured_value * self.calibration_factor
        return min(max(round(calibrated_value, 1), 0), self.max_irradiance)

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
                            (next_id, self.sensor_id, self.region_id, time_id, row['irradiance'])
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
            'irradiance': []
        }

        try:
            for _ in range(num_samples):
                timestamp = datetime.now()
                irradiance = self.simulate_irradiance()

                data['timestamp'].append(timestamp)
                data['irradiance'].append(irradiance)

        except KeyboardInterrupt:
            print("\nColeta interrompida pelo usuário")
        finally:
            df = pd.DataFrame(data)
            # print(f"\nColeta concluída. DataFrame gerado com {len(df)} amostras")
            # print(df.head())

            if save_to_db:
                self._save_to_mysql(df)

            return df


if __name__ == "__main__":
    from conection.MysqlConection import MySQLConnector

    mysql_config = {
        'host': 'localhost',
        'database': 'agrosync',
        'user': 'seu_usuario',
        'password': 'sua_senha'
    }
    mysql_connector = MySQLConnector(**mysql_config)

    sensor = ApogeeSP110Simulator(
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