from datetime import datetime
from pymysql import Error
import pandas as pd
import random
import psutil
import math

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
from datetime import datetime
from pymysql import Error
import pandas as pd
import random
import psutil
import math

class NPKSensorSimulator:
    """
    Simulador de sensor de NPK com capacidade de:
    - Simulação realista de concentrações de N, P e K no solo
    - Influência de chuva e temperatura nos níveis de nutrientes
    - Geração de DataFrame com os dados
    - Armazenamento no MySQL na tabela FatoValores (respeitando estrutura atual)
    """

    def __init__(self, sensor_id=None, region_id=None, mysql_connector=None):
        self.sensor_id = sensor_id
        self.region_id = region_id
        self.mysql_connector = mysql_connector
        self.last_temp = 25
        self.last_rain = 5

    def simulate_weather(self):
        temperatura = random.uniform(10, 40)
        chuva = max(0, random.gauss(5, 10))
        self.last_temp = round(temperatura, 1)
        self.last_rain = round(chuva, 1)

    def simulate_npk(self):
        self.simulate_weather()
        temperatura = self.last_temp
        chuva = self.last_rain

        nitrogenio = max(0, random.gauss(25, 10) - (chuva * 0.3 + max(0, temperatura - 35)))
        fosforo = max(0, random.gauss(12, 4) - (chuva * 0.1))
        potassio = max(0, random.gauss(120, 30) - (chuva * 0.2))

        return round(nitrogenio, 1), round(fosforo, 1), round(potassio, 1)

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
                        for valor in [row['nitrogenio'], row['fosforo'], row['potassio']]:
                            values.append((
                                self.sensor_id,
                                valor,
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
            'nitrogenio': [],
            'fosforo': [],
            'potassio': []
        }

        try:
            for _ in range(num_samples):
                timestamp = datetime.now()
                n, p, k = self.simulate_npk()

                data['timestamp'].append(timestamp)
                data['nitrogenio'].append(n)
                data['fosforo'].append(p)
                data['potassio'].append(k)

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

    sensor = NPKSensorSimulator(
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
