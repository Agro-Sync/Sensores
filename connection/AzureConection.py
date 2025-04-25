import time
import random
from azure.iot.device import IoTHubDeviceClient, Message

class AzureIotConnection:
    def __init__(self, connection_string=None):
        if connection_string is None:
            self.connection_string = 'HostName=Grupo09.azure-devices.net;DeviceId=TesteConectsSensor;SharedAccessKey=W2T8NbTMa7mN+86/Had4O3DbTudxACoKYJLNFXphuns='
        else:
            self.connection_string = connection_string
        self.device_client = None

    def connect(self):
        self.device_client = IoTHubDeviceClient.create_from_connection_string(self.connection_string)
        self.device_client.connect()
        print("Conectado ao Azure IoT Hub")

    def disconnect(self):
        if self.device_client:
            self.device_client.disconnect()
            print("Desconectado do Azure IoT Hub")

    def send_message(self, data):
        if self.device_client:
            message = Message(data)
            message.content_encoding = "utf-8"
            message.content_type = "application/json"
            self.device_client.send_message(message)
            print(f"Mensagem enviada: {data}")
