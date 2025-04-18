import random
import math
from datetime import datetime
import pandas as pd
from pymysql import Error

class EzoPhSensor:
    def __init__(self, sensor_id=None, region_id=None, mysql_connector=None):
        self.min_ph = 0.0
        self.max_ph = 14.0
        self.noise_level = 0.1
        self.sensor_id = sensor_id
        self.region_id = region_id
        self.mysql_connector = mysql_connector

    def simulate_ezo_ph_sensor(self):
        ph_value = random.uniform(self.min_ph, self.max_ph) 
        noise = random.uniform(-self.noise_level, self.noise_level)  
        simulated_ph = round(ph_value + noise, 2)
        return simulated_ph

    def collect_data(self, num_samples, save_to_db=False):
        data = {
            'timestamp': [],
            'ph': []
        }

        try:
            for _ in range(num_samples):
                timestamp = datetime.now()
                ph = self.simulate_ezo_ph_sensor()

                data['timestamp'].append(timestamp)
                data['ph'].append(ph)

        except KeyboardInterrupt:
            print("\nColeta interrompida pelo usuário")
        finally:
            df = pd.DataFrame(data)
            print(df)
            # print(f"\nColeta concluída. DataFrame gerado com {len(df)} amostras")
            # print(df.head())

            if save_to_db:
                self._save_to_mysql(df)

            return df

if __name__ == "__main__":
    
    mysql_config = {
        'host': 'localhost',
        'database': 'agrosync',
        'user': 'seu_usuario',
        'password': 'sua_senha'
    }
    mysql_connector = MySQLConnector(**mysql_config)

    sensor = ApogeeSP110Simulator(
        sensor_id=2,
        region_id=2,
        mysql_connector=mysql_connector
    )

    df = sensor.collect_data(
        num_samples=15,
        save_to_db=True
    )

    print("\nEstatísticas dos dados coletados:")
    print(df.describe())

