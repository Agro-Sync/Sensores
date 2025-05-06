import random
from simuladores.Sensor import Sensor


class NPKSensorSimulator(Sensor):
    """
    Simulador de sensor de NPK com capacidade de:
    - Simulação realista de concentrações de N, P e K no solo
    - Influência de chuva e temperatura nos níveis de nutrientes
    - Geração de DataFrame com os dados
    - Armazenamento no MySQL na tabela FatoValores (respeitando estrutura atual)
    """
    def __init__(self, sensor_id=None, region_id=None, mysql_connector=None):
        super().__init__(sensor_id, region_id, mysql_connector)
        self.last_temp = 25
        self.last_rain = 5

    @property
    def sensor_type(self):
        return 'NPK'

    def simulate_weather(self):
        temperatura = random.uniform(10, 40)
        chuva = max(0, random.gauss(5, 10))
        self.last_temp = round(temperatura, 1)
        self.last_rain = round(chuva, 1)

    def simulate_reading(self):
        self.simulate_weather()
        temperatura = self.last_temp
        chuva = self.last_rain

        nitrogenio = max(0, random.gauss(25, 10) - (chuva * 0.3 + max(0, temperatura - 35)))
        fosforo = max(0, random.gauss(12, 4) - (chuva * 0.1))
        potassio = max(0, random.gauss(120, 30) - (chuva * 0.2))

        return {
            "nitrogenio": round(nitrogenio, 1),
            "fosforo": round(fosforo, 1),
            "potassio": round(potassio, 1)
        }

    def _get_sensor_values(self, row):
        return [
            ('nitrogenio', row['nitrogenio']),
            ('fosforo', row['fosforo']),
            ('potassio', row['potassio'])
        ]

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
        save_to_db=False
    )

    print("\nEstatísticas dos dados coletados:")
    print(df.describe())
