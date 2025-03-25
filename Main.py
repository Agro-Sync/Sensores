from simuladores.ApogeeSP110Simulator import ApogeeSP110Simulator
from conection.MysqlConection import MySQLConnector

mysql_config = {
    'host': 'localhost',
    'database': 'agrosync',
    'user': 'usuario',
    'password': 'senha'
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