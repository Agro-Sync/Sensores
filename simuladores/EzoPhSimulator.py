import random
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

class EzoPhSensor:
    def __init__(self, sensor_id=None, region_id=None, mysql_connector=None):
        # Faixa típica de pH para solos de plantação de milho
        self.min_ph = 5.0
        self.max_ph = 7.5
        self.noise_level = 0.05  # Ruído reduzido para sensor de qualidade
        self.sensor_id = sensor_id
        self.region_id = region_id
        self.mysql_connector = mysql_connector
        self.calibration_status = "uncalibrated"  # uncalibrated, 1-point, 2-point, 3-point
        self.temperature = 25.0  # Temperatura padrão em °C
        self.sensor_age = 0  # Dias desde a última calibração
        self.probe_condition = 1.0  # 1.0 = nova, diminui com o tempo
        
        # Padrões diários de pH (variação circadiana)
        self.daily_pattern = interp1d(
            [0, 6, 12, 18, 24],  # Horas do dia
            [0, -0.1, 0.2, 0, 0],  # Variação de pH
            kind='quadratic',
            fill_value="extrapolate"
        )
        
        # Valores de calibração
        self.calibration_points = {
            'low': {'actual': 4.0, 'measured': None},
            'mid': {'actual': 7.0, 'measured': None},
            'high': {'actual': 10.0, 'measured': None}
        }

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
        
        self.sensor_age = 0  # Resetar idade após calibração
        print(f"Calibração de {point} ponto(s) concluída. Status: {self.calibration_status}")

    def apply_temperature_compensation(self, ph_value):
        """Aplica compensação de temperatura baseada no efeito térmico no sensor"""
        # Coeficiente típico de temperatura para eletrodos de pH: ~0.003 pH/°C
        temp_coeff = 0.003
        temp_diff = self.temperature - 25.0  # Diferença da temperatura de referência (25°C)
        return ph_value + (temp_diff * temp_coeff)

    def apply_daily_variation(self, ph_value, timestamp):
        """Aplica variação circadiana baseada na hora do dia"""
        hour = timestamp.hour + timestamp.minute/60
        daily_variation = self.daily_pattern(hour)
        return ph_value + daily_variation

    def simulate_ezo_ph_sensor(self, timestamp=None):
        """Simula a leitura do sensor EZO-pH com todos os fatores considerados"""
        if timestamp is None:
            timestamp = datetime.now()
            
        # Valor base do pH para solo de milho (levemente ácido)
        base_ph = random.uniform(5.8, 6.8)
        
        # Aplicar efeitos
        ph_value = base_ph
        ph_value = self.apply_daily_variation(ph_value, timestamp)
        ph_value = self.apply_temperature_compensation(ph_value)
        
        # Adicionar ruído eletrônico (menor quando calibrado)
        noise_factor = 0.5 if self.calibration_status == "uncalibrated" else 0.1
        noise = random.uniform(-self.noise_level, self.noise_level) * noise_factor
        ph_value += noise
        
        # Limitar à faixa possível
        ph_value = max(self.min_ph, min(self.max_ph, ph_value))
        
        # Arredondar para 2 casas decimais (precisão típica do EZO-pH)
        simulated_ph = round(ph_value, 2)
        
        return simulated_ph

    def collect_data(self, num_samples, interval_minutes=15, save_to_db=False):
        """Coleta dados simulados do sensor"""
        data = {
            'timestamp': [],
            'ph': [],
            'temperature': [],
            'sensor_id': [],
            'region_id': []
        }

        try:
            current_time = datetime.now()
            for _ in range(num_samples):
                timestamp = current_time
                ph = self.simulate_ezo_ph_sensor(timestamp)
                
                # Simular pequenas variações de temperatura
                self.temperature = 20 + 10 * np.sin(timestamp.hour/24 * 2 * np.pi) + random.uniform(-1, 1)
                
                data['timestamp'].append(timestamp)
                data['ph'].append(ph)
                data['temperature'].append(round(self.temperature, 1))
                data['sensor_id'].append(self.sensor_id)
                data['region_id'].append(self.region_id)
                
                current_time += timedelta(minutes=interval_minutes)
                
                # Simular envelhecimento do sensor durante a coleta
                self.sensor_age += interval_minutes / (60 * 24)  # Converter minutos em dias

        except KeyboardInterrupt:
            print("\nColeta interrompida pelo usuário")
        finally:
            df = pd.DataFrame(data)
            
            if save_to_db and self.mysql_connector:
                self.save_to_database(df)
            
            return df

    def save_to_database(self, df):
        """Simula o salvamento no banco de dados"""
        print(f"\nSimulando salvamento de {len(df)} amostras no banco de dados...")
        # Aqui iria o código para salvar no MySQL usando o mysql_connector
        print("Dados salvos com sucesso (simulação)")

    def plot_data(self, df):
        """Gera gráficos dos dados coletados"""
        print(df)
        plt.figure(figsize=(12, 6))
        
        # Gráfico de pH ao longo do tempo
        plt.subplot(1, 2, 1)
        plt.plot(df['timestamp'], df['ph'], 'b-', label='pH')
        plt.xlabel('Tempo')
        plt.ylabel('pH')
        plt.title('Variação de pH no solo ao longo do tempo')
        plt.grid(True)
        
        # Gráfico de temperatura
        plt.subplot(1, 2, 2)
        plt.plot(df['timestamp'], df['temperature'], 'r-', label='Temperatura (°C)')
        plt.xlabel('Tempo')
        plt.ylabel('Temperatura (°C)')
        plt.title('Temperatura durante a medição')
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    # Criar sensor simulando uma sonda nova, calibrada de 2 pontos
    sensor = EzoPhSensor(sensor_id=2, region_id=2)
    
    # Simular calibração (normalmente feito com soluções padrão de pH 4 e 7)
    sensor.calibrate(2, 4.0)  # Ponto baixo
    sensor.calibrate(2, 7.0)  # Ponto médio
    
    # Coletar dados por 2 dias a cada 30 minutos
    df = sensor.collect_data(
        num_samples=96,  # 48 horas * 2 amostras/hora
        interval_minutes=30,
        save_to_db=True
    )

    # Mostrar estatísticas
    print("\nEstatísticas dos dados coletados:")
    print(df.describe())
    
    # Plotar gráficos
    sensor.plot_data(df)