import os
from datetime import datetime
from pymysql import Error
import pandas as pd
import random
import psutil
import json

from simuladores.Sensor import Sensor


class SHT31Simulator(Sensor):
    """
    Simulador do sensor Sensirion SHT31 com capacidade de:
    - Simulação realista de humidade relativa do ar
    - Geração de DataFrame com os dados
    - Armazenamento no MySQL na tabela FatoValores
    """
    def __init__(self, sensor_id=None, region_id=None, mysql_connector=None):
        super().__init__(sensor_id, region_id, mysql_connector)
        self.max_humidity = 100
        self.calibration_factor = 1.0

    @property
    def sensor_type(self):
        return 'SHT31'

    def calibrate(self, calibration_factor=1.0):
        self.calibration_factor = calibration_factor
        print(f"Sensor calibrado com fator {calibration_factor:.2f}")

    def simulate_reading(self, base_value=None):
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
        return {
            "humidity": min(max(round(calibrated_value, 1), 0), self.max_humidity)
        }

    def _get_sensor_values(self, row):
        return [("humidity", row["humidity"]),]

if __name__ == "__main__":
    from connection import MySQLConnector

    mysql_config = {
        'host': 'localhost',
        'database': 'agrosync',
        'user': 'seu_usuario',
        'password': 'sua_senha'
    }
    mysql_connector = MySQLConnector(**mysql_config)

    sensor = SHT31Simulator(
        sensor_id=1,
        region_id=1,
        mysql_connector=mysql_connector
    )

    df = sensor.collect_data(
        num_samples=15,
        save_to_db=False
    )

    print("\nEstatísticas dos dados coletados:")
    print(df.describe())