import random
import math
from datetime import datetime
from simuladores.Sensor import Sensor

class ApogeeSP110Simulator(Sensor):
    """
    Simulador do sensor Apogee SP-110 com capacidade de:
    - Simulação realista de irradiância solar
    - Geração de DataFrame com os dados
    - Armazenamento no MySQL na tabela FatoValores
    """
    def __init__(self, sensor_id=None, region_id=None, mysql_connector=None):
        super().__init__(sensor_id, region_id, mysql_connector)
        self.max_irradiance = 2000
        self.calibration_factor = 1.0

    @property
    def sensor_type(self):
        return 'ApogeeSP110'

    def calibrate(self, calibration_factor=1.0):
        self.calibration_factor = calibration_factor
        print(f"Sensor calibrado com fator {calibration_factor:.2f}")

    def simulate_reading(self, base_value=None):
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
        return {
            "irradiance": min(max(round(calibrated_value, 1), 0), self.max_irradiance)
        }

    def _get_sensor_values(self, row):
        return [(None, row['irradiance'])]

if __name__ == "__main__":
    from connection import MySQLConnector

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