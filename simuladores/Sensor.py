from abc import ABC, abstractmethod
from datetime import datetime
from typing import final

from pymysql import Error
import os
import json
import psutil
import pandas as pd

class Sensor(ABC):
    def __init__(self, sensor_id=None, region_id=None, mysql_connector=None):
        self.sensor_id = sensor_id
        self.region_id = region_id
        self.mysql_connector = mysql_connector
        self.sensor_name = self.__class__.__name__

    @property
    @abstractmethod
    def sensor_type(self):
        """Propriedade abstrata que retorna o tipo do sensor"""
        pass

    @staticmethod
    @final
    def _get_system_metrics():
        process = psutil.Process(os.getpid())
        return {
            'cpu_usage': psutil.cpu_percent(),
            'mem_mb': process.memory_info().rss / (1024 * 1024)
        }

    @staticmethod
    def _execute_batch_insert(cursor, values):
        query = """
            INSERT INTO agrosync.log_exec 
            (id_sensor, valor, dt_exec, dt_start_exec, dt_end_exec, qtd_data, ram_usage, process_usage, sensor_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
        cursor.executemany(query, values)

    @final
    def _save_to_mysql(self, data_frame, num_sample):
        if not all([self.mysql_connector, self.sensor_id is not None, self.region_id is not None]):
            print("Configuração MySQL incompleta - pulando salvamento no banco")
            return False

        try:
            with self.mysql_connector.get_connection() as conn:
                with conn.cursor() as cursor:
                    metrics = self._get_system_metrics()
                    values = []

                    for _, row in data_frame.iterrows():
                        time_init = row['timestamp']
                        for element_name, valor in self._get_sensor_values(row):
                            values.append((
                                self.sensor_id,
                                valor,
                                time_init.strftime('%Y-%m-%d'),
                                time_init,
                                datetime.now(),
                                num_sample,
                                round(metrics['mem_mb'], 2),
                                metrics['cpu_usage'],
                                f"{self.sensor_type} {element_name}" if element_name else self.sensor_type
                            ))
                    self._execute_batch_insert(cursor, values)
                    conn.commit()

        except Error as e:
            print(f"Erro ao salvar no MySQL: {e}")
            return False

    @final
    def _save_to_json(self, data_frame, num_sample, file_path='dados_sensores.json'):
        metrics = self._get_system_metrics()
        json_data = []

        for _, row in data_frame.iterrows():
            time_init = row['timestamp']

            for element_name, valor in self._get_sensor_values(row):
                json_data.append({
                    "id_sensor": self.sensor_id,
                    "valor": valor,
                    "dt_exec": time_init.strftime('%Y-%m-%d'),
                    "dt_start_exec": time_init.isoformat(),
                    "dt_end_exec": datetime.now().isoformat(),
                    "qtd_data": num_sample,
                    "ram_usage": round(metrics['mem_mb'], 2),
                    "process_usage": metrics['cpu_usage'],
                    "sensor_name": f"{self.sensor_type} {element_name}" if element_name else self.sensor_type
                })

        # self._save_in_file(file_path, json_data)
        return json_data

    @abstractmethod
    def _get_sensor_values(self, row):
        """Método abstrato que deve retornar uma lista de tuplas (nome_elemento, valor)"""
        pass

    @staticmethod
    @final
    def _save_in_file(file_path, json_data):
        file_exists = os.path.exists(file_path)

        with open(file_path, 'a', encoding='utf-8') as f:
            if file_exists:
                f.write(",")
            for i, data in enumerate(json_data):
                if i > 0:
                    f.write(',\n')
                json.dump(data, f, separators=(',',':'), ensure_ascii=False)


    @final
    def collect_data(self, num_samples, file_name='dados_sensores.json', save_to_db=False):
        data = {'timestamp': []}

        try:
            for _ in range(num_samples):
                timestamp = datetime.now()
                readings = self.simulate_reading()

                data['timestamp'].append(timestamp)
                for key, value in readings.items():
                    if key not in data:
                        data[key] = []
                    data[key].append(value)

        except KeyboardInterrupt:
            print("\nColeta interrompida pelo usuário")
        finally:
            df = pd.DataFrame(data)
            payload = self._save_to_json(df, num_samples, file_name)
            if save_to_db:
                self._save_to_mysql(df, num_samples)
            return payload

    @abstractmethod
    def simulate_reading(self):
        """Método abstrato que deve retornar um dicionário com as leituras"""
        pass