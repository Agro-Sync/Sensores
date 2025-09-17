import json
import time
import requests
from simuladores import *

URL = "http://ec2-18-207-21-79.compute-1.amazonaws.com:8080/publish"

apogee = ApogeeSP110Simulator(
    sensor_id=1,
    region_id=1,
)
npk = NPKSensorSimulator(
    sensor_id=2,
    region_id=1,
)
decagon = DecagonEC5Simulator(
    sensor_id=3,
    region_id=1,
)
sensirion = SHT31Simulator(
    sensor_id=4,
    region_id=1,
)
davis = Davis6410Simulator(
    sensor_id=5,
    region_id=1,
)
ezo = EzoPhSensor(
    sensor_id=6,
    region_id=1,
)
ezo.calibrate(2, 4.0)  # Ponto baixo
ezo.calibrate(2, 7.0)  # Ponto médio

def processar_bloco(tamanho_bloco):
    payload = {}

    sensores = {
        "Apogee": apogee,
        "NPK": npk,
        "Decagon": decagon,
        "SHT31": sensirion,
        "Davis": davis,
        "Ezo": ezo,
    }

    for nome, sensor in sensores.items():
        payload[nome] =  sensor.collect_data(num_samples=tamanho_bloco,save_to_db=False); # ; tem que ficar para não printar no jupyter

    return payload


def enviar_dado(payload):
    """Envia o dado para a API"""
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(URL, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            print(f"✅ Sucesso: {response.text}")
        else:
            print(f"⚠️ Erro {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Falha ao enviar: {e}")


if __name__ == "__main__":

    while True:
        payload = processar_bloco(tamanho_bloco=5)
        enviar_dado(payload)
        time.sleep(5)