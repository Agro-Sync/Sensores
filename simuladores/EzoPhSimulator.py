import random
from datetime import datetime
from simuladores.Sensor import Sensor
from scipy.interpolate import interp1d


class EzoPhSensor(Sensor):
    def __init__(self, sensor_id=None, region_id=None, mysql_connector=None):
        super().__init__(sensor_id, region_id, mysql_connector)

        self.min_ph = 5.0
        self.max_ph = 7.5
        self.noise_level = 0.05  # Ruído reduzido para sensor de qualidade
        self.calibration_status = "uncalibrated"  # uncalibrated, 1-point, 2-point, 3-point
        self.temperature = 25.0  # Temperatura padrão em °C
        self.sensor_age = 0  # Dias desde a última calibração
        self.probe_condition = 1.0  # 1.0 = nova, diminui com o tempo

        self.daily_pattern = interp1d(
            [0, 6, 12, 18, 24],  # Horas do dia
            [0, -0.1, 0.2, 0, 0],  # Variação de pH
            kind='quadratic',
            fill_value="extrapolate"
        )
        
        self.calibration_points = {
            'low': {'actual': 4.0, 'measured': None},
            'mid': {'actual': 7.0, 'measured': None},
            'high': {'actual': 10.0, 'measured': None}
        }

    @property
    def sensor_type(self):
        return "EzoPhSensor"

    def calibrate(self, point, actual_ph, measured_ph=None):
        """Simula o processo de calibração do sensor"""
        if point == 1:
            self.calibration_points['mid']['measured'] = actual_ph if measured_ph is None else measured_ph
            self.calibration_status = "1-point"
        elif point == 2:
            self.calibration_points['low']['measured'] = actual_ph if measured_ph is None else measured_ph
            self.calibration_status = "2-point"
        elif point == 3:
            self.calibration_points['high']['measured'] = actual_ph if measured_ph is None else measured_ph
            self.calibration_status = "3-point"

        self.sensor_age = 0
        # print(f"Calibração de {point} ponto(s) concluída. Status: {self.calibration_status}")

    def apply_temperature_compensation(self, ph_value):
        """Aplica compensação de temperatura"""
        temp_coeff = 0.003
        temp_diff = self.temperature - 25.0
        return ph_value + (temp_diff * temp_coeff)

    def apply_daily_variation(self, ph_value, timestamp):
        """Aplica variação circadiana"""
        hour = timestamp.hour + timestamp.minute / 60
        daily_variation = self.daily_pattern(hour)
        return ph_value + daily_variation

    def simulate_reading(self):
        """Implementação do método abstrato da classe base"""
        timestamp = datetime.now()

        # Valor base do pH para solo de milho
        base_ph = random.uniform(5.8, 6.8)

        # Aplicar efeitos
        ph_value = base_ph
        ph_value = self.apply_daily_variation(ph_value, timestamp)
        ph_value = self.apply_temperature_compensation(ph_value)

        # Adicionar ruído
        noise_factor = 0.5 if self.calibration_status == "uncalibrated" else 0.1
        noise = random.uniform(-self.noise_level, self.noise_level) * noise_factor
        ph_value += noise

        # Limitar à faixa possível
        ph_value = max(self.min_ph, min(self.max_ph, ph_value))

        return {
            'ph': round(ph_value, 2),
            'temperature': self.temperature
        }

    def _get_sensor_values(self, row):
        """Implementação do método abstrato para obtenção dos valores"""
        return [
            ('pH', row['ph']),
            ('Temperature', row['temperature'])
        ]
if __name__ == "__main__":
    from connection import MySQLConnector  # Sua classe de conexão

    mysql_connector = MySQLConnector(
        host='localhost',
        database='agrosync',
        user='seu_usuario',
        password='sua_senha'
    )

    sensor = EzoPhSensor(
        sensor_id=2,
        region_id=2,
        mysql_connector=mysql_connector
    )
    
    sensor.calibrate(2, 4.0)  # Ponto baixo
    sensor.calibrate(2, 7.0)  # Ponto médio
    
    df = sensor.collect_data(
        num_samples=20,
        save_to_db=False
    )

    # Mostrar estatísticas
    print("\nEstatísticas dos dados coletados:")
    print(df.describe())
