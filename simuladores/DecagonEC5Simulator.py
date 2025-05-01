import random
import math
from datetime import datetime
from simuladores.Sensor import Sensor


class DecagonEC5Simulator(Sensor):
    """
    Simulador do sensor de Umidade do Solo com capacidade de:
    - Simulação realista de umidade do solo
    - Geração de DataFrame com os dados
    - Armazenamento no MySQL na tabela FatoValores
    """
    def __init__(self, sensor_id=None, region_id=None, mysql_connector=None):
        super().__init__(sensor_id, region_id, mysql_connector)
        self.max_moisture = 100
        self.calibration_factor = 1.0

    @property
    def sensor_type(self):
        return 'DecagonEC5'

    def calibrate(self, calibration_factor=1.0):
        self.calibration_factor = calibration_factor
        print(f"Sensor calibrado com fator {calibration_factor:.2f}")

    def simulate_reading(self, base_value=None):
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
        return {
            "umidade":min(max(round(calibrated_value, 1), 0), self.max_moisture)
        }

    def _get_sensor_values(self, row):
        return {(None, row['umidade'])}

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
