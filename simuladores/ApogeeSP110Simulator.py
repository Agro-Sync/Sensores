import random
import time
import csv
import math
import matplotlib.pyplot as plt
from datetime import datetime
import pymysql
from pymysql import Error

class ApogeeSP110Simulator:
    """
    Simulador do sensor Apogee SP-110 com capacidade de:
    - Simulação realista de irradiância solar
    - Salvar dados em CSV
    - Plotar gráficos
    - Armazenar no MySQL na tabela FatoValores
    """
    
    def __init__(self, sample_rate=1, sensor_id=None, region_id=None, mysql_connector=None):
        self.sample_rate = sample_rate
        self.max_irradiance = 2000  # W/m²
        self.calibration_factor = 1.0
        self.is_running = False
        self.sensor_id = sensor_id
        self.region_id = region_id
        self.mysql_connector = mysql_connector
        
    def calibrate(self, calibration_factor=1.0):
        self.calibration_factor = calibration_factor
        print(f"Sensor calibrado com fator {calibration_factor:.2f}")
        
    def simulate_irradiance(self, base_value=None):
        if base_value is None:
            now = datetime.now()
            hour = now.hour + now.minute/60 + now.second/3600
            
            if 5 <= hour <= 19:
                solar_angle = math.pi * (hour - 12) / 15
                max_irradiance = 1000  # W/m²
                base_value = max_irradiance * math.sin(math.pi/2 - abs(solar_angle))**1.5
                base_value = max(0, base_value)
                
                if hour < 6 or hour > 18:
                    base_value *= 0.3 * (1 - abs(hour - 12)/6)
            else:
                base_value = random.uniform(0, 10)
        else:
            base_value = min(max(base_value, 0), self.max_irradiance)
        
        noise = random.gauss(0, base_value * 0.02 + 2)
        max_variation = base_value * 0.05 + 5
        measured_value = base_value + max(-max_variation, min(noise, max_variation))
        calibrated_value = measured_value * self.calibration_factor
        return min(max(round(calibrated_value, 1), 0), self.max_irradiance)
    
    def _get_time_id(self, timestamp):
        return int(timestamp.strftime("%Y%m%d%H"))
    
    def _save_to_mysql(self, timestamp, value):
        if not all([self.mysql_connector, self.sensor_id is not None, self.region_id is not None]):
            print("Configuração MySQL incompleta - pulando salvamento no banco")
            return False
            
        time_id = self._get_time_id(timestamp)
        
        try:
            next_id = self.mysql_connector.get_next_id('agrosync.FatoValores', 'idValor')
            
            success = self.mysql_connector.execute_query(
                "INSERT INTO agrosync.FatoValores (idValor, idSensor, idRegiao, idTempo, valor) "
                "VALUES (%s, %s, %s, %s, %s)",
                (next_id, self.sensor_id, self.region_id, time_id, value)
            )

            if success:
                print(f"Dados salvos no MySQL (ID: {next_id})")
                return True
            return False
                
        except Error as e:
            print(f"Erro ao salvar no MySQL: {e}")
            return False
    
    def _save_to_csv(self, timestamps, irradiance_values, filename):
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Timestamp', 'Irradiance (W/m²)'])
                for ts, val in zip(timestamps, irradiance_values):
                    writer.writerow([ts.strftime('%Y-%m-%d %H:%M:%S'), val])
            print(f"Dados salvos em {filename}")
        except Exception as e:
            print(f"Erro ao salvar CSV: {e}")
    
    def _plot_data(self, timestamps, irradiance_values):
        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, irradiance_values, 'b-')
        plt.title('Dados Simulados do Sensor Apogee SP-110')
        plt.xlabel('Tempo')
        plt.ylabel('Irradiância Solar (W/m²)')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    
    def collect_data(self, duration, filename=None, plot=False, save_to_db=False):
        self.is_running = True
        start_time = time.time()
        timestamps = []
        irradiance_values = []
        
        print(f"Iniciando coleta por {duration} segundos...")
        
        try:
            while (time.time() - start_time) < duration and self.is_running:
                timestamp = datetime.now()
                irradiance = self.simulate_irradiance()
                
                timestamps.append(timestamp)
                irradiance_values.append(irradiance)
                
                print(f"{timestamp.strftime('%H:%M:%S')} - {irradiance} W/m²")
                
                if save_to_db:
                    self._save_to_mysql(timestamp, irradiance)
                
                time.sleep(self.sample_rate)
                
        except KeyboardInterrupt:
            print("\nColeta interrompida pelo usuário")
        finally:
            self.is_running = False
            print(f"Coleta concluída. Total: {len(irradiance_values)} amostras")
            
            if filename:
                self._save_to_csv(timestamps, irradiance_values, filename)
                
            if plot:
                self._plot_data(timestamps, irradiance_values)


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
        sample_rate=2,
        sensor_id=1,
        region_id=1,
        mysql_connector=mysql_connector
    )
    
    # Testa a conexão MySQL separadamente
    with mysql_connector.get_connection() as conn:
        print("Conexão MySQL estabelecida com sucesso!")
    
    # Coleta dados com todas as funcionalidades
    sensor.collect_data(
        duration=30,
        filename='dados_sensor.csv',
        plot=True,
        save_to_db=True
    )