import random
from simuladores.Sensor import Sensor


class Davis6410Simulator(Sensor):
    """
    Simulador do sensor Anemômetro Davis 6410:
    - Simula velocidade e direção do vento
    - Geração de DataFrame com os dados
    - Armazenamento no MySQL na tabela FatoValores
    """
    def __init__(self, sensor_id=None, region_id=None, mysql_connector=None):
        super().__init__(sensor_id, region_id, mysql_connector)

    @property
    def sensor_type(self):
        return 'Davis6410'

    @staticmethod
    def simulate_wind_speed():
        """
        Simula a velocidade do vento em m/s, com base em distribuição normal truncada.
        """
        base_speed = random.gauss(5, 2)  
        base_speed = max(0, min(base_speed, 30))  
        return round(base_speed, 2)

    @staticmethod
    def simulate_wind_direction(prev_direction=None):
        """
        Simula a direção do vento em graus (0 a 360), com variação gradual.
        """
        if prev_direction is None:
            return round(random.uniform(0, 360), 2)
        variation = random.gauss(0, 10)  
        new_direction = (prev_direction + variation) % 360
        return round(new_direction, 2)

    def simulate_reading(self):
        return {
            "wind_speed": self.simulate_wind_speed(),
            "wind_direction": self.simulate_wind_direction()
        }

    def _get_sensor_values(self, row):
        return [
            ('wind_speed', row['wind_speed']),
            ('wind_direction', row['wind_direction'])
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

    sensor = Davis6410Simulator(
        sensor_id=2,
        region_id=1,
        mysql_connector=mysql_connector
    )

    df = sensor.collect_data(
        num_samples=20,
        save_to_db=True
    )

    print("\nEstatísticas dos dados coletados:")
    print(df.describe())
