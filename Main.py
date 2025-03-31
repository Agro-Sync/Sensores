from simuladores.ApogeeSP110Simulator import ApogeeSP110Simulator

mysql_config = {
    'host': 'localhost',
    'database': 'agrosync',
    'user': 'root',
    'password': 'sua_senha'
}

sensor = ApogeeSP110Simulator(
    sample_rate=2,
    sensor_id=1,
    region_id=1,
    mysql_connector=MySQLConnector(**mysql_config)
)

df = sensor.collect_data(
    duration=60,
    filename='dados_sensor.csv',
    plot=True,
    save_to_db=True
)

print("\nEstatísticas dos dados coletados:")
print(df.describe())