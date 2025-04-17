import time
import rando 
from azure.iot.device import IoTHubDeviceClient, Message


class AzureConnection:

    def connect(self, Connection_String = none, device_client = none, message = none):
        Connection_String = "HostName=Grupo09.azure-devices.net;DeviceId=TesteConectsSensor;SharedAccessKey=W2T8NbTMa7mN+86/Had4O3DbTudxACoKYJLNFXphuns="
        device_client = IoTHubDeviceClient.create_from_connection_string(Connection_String)
        device_client.connect()


    def disconnect(self, device_client):
        device_client.disconnect()
        print("Disconnected from Azure IoT Hub")

