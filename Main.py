from simuladores.ApogeeSP110Simulator import ApogeeSP110Simulator

mysql_config = {
    'host': 'localhost',
    'database': 'agrosync',
    'user': 'seu_usuario',
    'password': 'sua_senha'
}

sensor = ApogeeSP110Simulator(
    sensor_id=1,       
    region_id=1,       
    mysql_config=mysql_config
)

sensor.collect_data(
    duration=30,
    filename='dados_sensor.csv',
    plot=True,
    save_to_db=True
)