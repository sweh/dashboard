import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import PV
from influxdb import InfluxDBClient
import sys
from influxdb.client import InfluxDBClientError

START = datetime.datetime(2021, 2, 1, 0, 0, 0)
END = datetime.datetime(2021, 3, 1, 0, 0, 0)

db = 'dashboard'
host = 'localhost'
port = 8086
ssl = False
timeout = 5
user = 'sma'
password = 'sma'

engine = create_engine(
    'postgresql://club:wk6RwbEbxixGK8C4m69@localhost/dashboard'
)
session = sessionmaker(bind=engine)()

for item in (
    session.query(PV)
    .filter(PV._timestamp >= START)
    .filter(PV._timestamp < END)
    .order_by(PV._timestamp.desc())
):
    try:
        if ssl is True:
            influx = InfluxDBClient(
                host=host, port=port, ssl=ssl, verify_ssl=ssl,
                username=user, password=password, timeout=timeout
            )
        else:
            influx = InfluxDBClient(
                host=host, port=port, username=user, password=password,
                timeout=timeout
            )

        dbs = influx.get_list_database()
        if not {"name": db} in dbs:
            influx.create_database(db)

        influx.switch_database(db)

    except InfluxDBClientError as e:
        print(
            "InfluxDB:  Connect Error to '%s' @ '%s'(%s)" % (
                str(user), host, db)
        )
        print(format(e))
        sys.exit()
    except Exception as e:
        print(
            "InfluxDB: Error while connecting to '%s' @ '%s'(%s)" % (
                str(user), host, db)
        )
        print(e)
        sys.exit()

    result = {
        'Power from grid': int(item.power_from_grid),
        'Power to grid': int(item.power_to_grid),
        'AC Power Solar': int(item.ac_power_solar),
        'AC Power Battery': int(item.ac_power_battery),
        'Consumption': int(item.consumption),
        'BatteryCharge': float(item.battery_charge),
        'BatteryTemp': item.battery_temp,
    }

    influx_data = {}
    influx_data['measurement'] = 'PV'
    influx_data['time'] = item._timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
    influx_data['tags'] = {}
    influx_data['fields'] = result

    points = [influx_data]
    influx.write_points(points, time_precision='s', protocol='json')

