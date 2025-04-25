import matplotlib.pyplot as plt
from connection import MySQLConnector
from simuladores import *
import time
import sys
from conection import AzureIotConnection

mysql_config = {
    'host': 'localhost',
    'database': 'agrosync',
    'user': 'seu_usuario',
    'password': 'sua_senha'
}

mysql_connector = MySQLConnector(**mysql_config)
azure = AzureIotConnection()
azure.connect()

apogee = ApogeeSP110Simulator(
    sensor_id=1,
    region_id=1,
    mysql_connector=mysql_connector
)
npk = NPKSensorSimulator(
    sensor_id=2,
    region_id=1,
    mysql_connector=mysql_connector
)
decagon = DecagonEC5Simulator(
    sensor_id=3,
    region_id=1,
    mysql_connector=mysql_connector
)
sensirion = SHT31Simulator(
    sensor_id=4,
    region_id=1,
    mysql_connector=mysql_connector
)

def processar_bloco(tamanho_bloco):
    tempos = {}
    memorias = {}

    sensores = {
        "Apogee": apogee,
        "NPK": npk,
        "Decagon": decagon,
        "SHT31": sensirion
    }

    for nome, sensor in sensores.items():
        inicio = time.time()
        df = sensor.collect_data(num_samples=tamanho_bloco, save_to_db=True)
        fim = time.time()

        for _, row in df.iterrows():
            row_json = row.to_json()
            azure.send_message(row_json)    

        tempos[nome] = fim - inicio
        memorias[nome] = sys.getsizeof(df) / (1024 * 1024)

    return tempos, memorias

def plot_individual_por_sensor(tamanhos, tempos_sensor, mem_sensor):
    for sensor in tempos_sensor.keys():
        plt.figure(figsize=(14, 6))

        # Tempo
        plt.subplot(1, 2, 1)
        for i, tempo_cenario in enumerate(tempos_sensor[sensor]):
            plt.plot(tamanhos[i], tempo_cenario, marker='o', label=f'Cenário {chr(97 + i)}')
        plt.title(f'Tempo de Execução - {sensor}')
        plt.xlabel('Tamanho do Bloco')
        plt.ylabel('Tempo (s)')
        plt.legend()
        plt.grid()

        # Memória
        plt.subplot(1, 2, 2)
        for i, mem_cenario in enumerate(mem_sensor[sensor]):
            plt.plot(tamanhos[i], mem_cenario, marker='o', label=f'Cenário {chr(97 + i)}')
        plt.title(f'Uso de Memória - {sensor}')
        plt.xlabel('Tamanho do Bloco')
        plt.ylabel('Memória (MB)')
        plt.legend()
        plt.grid()

        plt.suptitle(f"Desempenho do Sensor {sensor}", fontsize=14)
        plt.tight_layout()
        plt.show()


def plot_desempenho_geral_por_cenario(tamanhos_por_cenario, tempos_por_sensor, mem_por_sensor):
    for i, tamanhos in enumerate(tamanhos_por_cenario):
        plt.figure(figsize=(14, 6))

        # Tempo total do cenário i
        tempos_totais = [
            sum(tempos_por_sensor[sensor][i][j] for sensor in tempos_por_sensor)
            for j in range(len(tamanhos))
        ]

        # Memória total do cenário i
        memorias_totais = [
            sum(mem_por_sensor[sensor][i][j] for sensor in mem_por_sensor)
            for j in range(len(tamanhos))
        ]

        # Gráfico de tempo
        plt.subplot(1, 2, 1)
        plt.plot(tamanhos, tempos_totais, marker='o', color='tab:blue')
        plt.title(f"Tempo Total por Bloco - Cenário {chr(97 + i)}")
        plt.xlabel("Tamanho do Bloco")
        plt.ylabel("Tempo Total (s)")
        plt.grid()

        # Gráfico de memória
        plt.subplot(1, 2, 2)
        plt.plot(tamanhos, memorias_totais, marker='o', color='tab:orange')
        plt.title(f"Uso Total de Memória - Cenário {chr(97 + i)}")
        plt.xlabel("Tamanho do Bloco")
        plt.ylabel("Memória Total (MB)")
        plt.grid()

        plt.suptitle(f"Desempenho Geral - Cenário {chr(97 + i)}", fontsize=14)
        plt.tight_layout()
        plt.show()


def plot_por_cenario(tamanhos_por_cenario, tempos_sensor, mem_sensor):
    for i, tamanhos in enumerate(tamanhos_por_cenario):
        plt.figure(figsize=(14, 6))

        # Tempo por sensor
        plt.subplot(1, 2, 1)
        for nome in tempos_sensor:
            plt.plot(tamanhos, tempos_sensor[nome][i], marker='o', label=nome)
        plt.title(f"Tempo de Execução - Cenário {chr(97 + i)}")
        plt.xlabel("Tamanho do Bloco")
        plt.ylabel("Tempo (s)")
        plt.legend()
        plt.grid()

        # Memória por sensor
        plt.subplot(1, 2, 2)
        for nome in mem_sensor:
            plt.plot(tamanhos, mem_sensor[nome][i], marker='o', label=nome)
        plt.title(f"Uso de Memória - Cenário {chr(97 + i)}")
        plt.xlabel("Tamanho do Bloco")
        plt.ylabel("Memória (MB)")
        plt.legend()
        plt.grid()

        plt.suptitle(f"Desempenho por Sensor - Cenário {chr(97 + i)}", fontsize=14)
        plt.tight_layout()
        plt.show()


cenarios = [
    range(100, 600, 100),
    range(1000, 6000, 100),
    range(100, 600, 100),
]

tempos_por_sensor = {nome: [] for nome in ["Apogee", "NPK", "Decagon", "SHT31"]}
memorias_por_sensor = {nome: [] for nome in ["Apogee", "NPK", "Decagon", "SHT31"]}
tamanhos_por_cenario = []

# Processa cada cenário
for cenario in cenarios:
    # Temporários para este cenário
    temp_sensor = {nome: [] for nome in tempos_por_sensor}
    mem_sensor = {nome: [] for nome in memorias_por_sensor}
    tamanhos = []

    for tamanho in cenario:
        tempos, memorias = processar_bloco(tamanho)
        for nome in tempos:
            temp_sensor[nome].append(tempos[nome])
            mem_sensor[nome].append(memorias[nome])
        tamanhos.append(tamanho)

    tamanhos_por_cenario.append(tamanhos)

    for nome in tempos_por_sensor:
        tempos_por_sensor[nome].append(temp_sensor[nome])
        memorias_por_sensor[nome].append(mem_sensor[nome])


# Plotagem dos gráficos
plot_individual_por_sensor(tamanhos_por_cenario, tempos_por_sensor, memorias_por_sensor)
plot_desempenho_geral_por_cenario(tamanhos_por_cenario, tempos_por_sensor, memorias_por_sensor)
plot_por_cenario(tamanhos_por_cenario, tempos_por_sensor, memorias_por_sensor)

azure.disconnect()