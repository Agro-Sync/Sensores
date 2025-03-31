import matplotlib.pyplot as plt
from conection.MysqlConection import MySQLConnector
from simuladores.ApogeeSP110Simulator import ApogeeSP110Simulator
import time
import sys

mysql_config = {
    'host': 'localhost',
    'database': 'agrosync',
    'user': 'root',
    'password': 'sua_senha'
}

sensor = ApogeeSP110Simulator(
    sensor_id=1,
    region_id=1,
    mysql_connector=MySQLConnector(**mysql_config)
)


def processar_bloco(tamanho_bloco):
    inicio_tempo = time.time()

    df = sensor.collect_data(
        num_samples=tamanho_bloco,
        save_to_db=False
    )

    fim_tempo = time.time()
    tempo_execucao = fim_tempo - inicio_tempo

    uso_memoria = sys.getsizeof(df) / (1024 * 1024)

    return tempo_execucao, uso_memoria


def plot_graficos(tamanhos, tempos, memorias, cenarios):
    plt.figure(figsize=(14, 6))

    plt.subplot(1, 2, 1)
    for i, cenario in enumerate(cenarios):
        plt.plot(tamanhos[i], tempos[i], marker='o', label=f'Cenário {chr(97 + i)}')
    plt.title('Tempo de Execução vs Tamanho do Bloco')
    plt.xlabel('Tamanho do Bloco')
    plt.ylabel('Tempo de Execução (s)')
    plt.legend()
    plt.grid()

    # Gráfico de Uso de Memória
    plt.subplot(1, 2, 2)
    for i, cenario in enumerate(cenarios):
        plt.plot(tamanhos[i], memorias[i], marker='o', label=f'Cenário {chr(97 + i)}')
    plt.title('Uso de Memória vs Tamanho do Bloco')
    plt.xlabel('Tamanho do Bloco')
    plt.ylabel('Uso de Memória (MB)')
    plt.legend()
    plt.grid()

    plt.tight_layout()
    plt.show()


cenarios = [
    range(100, 600, 100),
    range(1000, 6000, 100),
    range(100, 600, 100),
]


tamanhos_por_cenario = []
tempos_por_cenario = []
memorias_por_cenario = []

# Processa cada cenário
for cenario in cenarios:
    tempos = []
    memorias = []
    tamanhos = []
    for tamanho in cenario:
        tempo, memoria = processar_bloco(tamanho)
        tempos.append(tempo)
        memorias.append(memoria)
        tamanhos.append(tamanho)
    tempos_por_cenario.append(tempos)
    memorias_por_cenario.append(memorias)
    tamanhos_por_cenario.append(tamanhos)


# Plotagem dos gráficos
plot_graficos(tamanhos_por_cenario, tempos_por_cenario, memorias_por_cenario, cenarios)

# Identificação do pior e melhor caso
# for i, cenario in enumerate(cenarios):
#     indice_pior_tempo = tempos_por_cenario[i].index(max(tempos_por_cenario[i]))
#     indice_melhor_tempo = tempos_por_cenario[i].index(min(tempos_por_cenario[i]))
#
#     print(f"Cenário {chr(97 + i)}:")
#     print(f"  Pior caso (tempo): Tamanho {tamanhos_por_cenario[i][indice_pior_tempo]} - {tempos_por_cenario[i][indice_pior_tempo]:.2f} s")
#     print(f"  Melhor caso (tempo): Tamanho {tamanhos_por_cenario[i][indice_melhor_tempo]} - {tempos_por_cenario[i][indice_melhor_tempo]:.2f} s")
#
#     indice_pior_memoria = memorias_por_cenario[i].index(max(memorias_por_cenario[i]))
#     indice_melhor_memoria = memorias_por_cenario[i].index(min(memorias_por_cenario[i]))
#
#     print(f"  Pior caso (memória): Tamanho {tamanhos_por_cenario[i][indice_pior_memoria]} - {memorias_por_cenario[i][indice_pior_memoria]:.2f} MB")
#     print(f"  Melhor caso (memória): Tamanho {tamanhos_por_cenario[i][indice_melhor_memoria]} - {memorias_por_cenario[i][indice_melhor_memoria]:.2f} MB")
#     print()