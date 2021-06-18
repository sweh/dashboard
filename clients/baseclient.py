import asyncio
from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError
from datetime import datetime
from history import History
import json
import time
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class BaseClient:

    sleep_time = 60
    keep_items = 1
    history = None
    websockets = None
    external = False
    enabled = False
    external_operation_time = ('05:30', '22:30')
    type_ = None

    def __init__(self, config):
        self.config = config
        self.enabled = bool(int(config.get(self.type_.upper(), 'enabled')))
        self.history = History(
            self.type_,
            config.engine,
            max_items=self.keep_items
        )
        self.websockets = {}

    async def register(self, websocket):
        self.websockets[websocket] = []
        for item in self.history:
            await self.send(websocket, item)

    async def send(self, websocket, data):
        if data in self.websockets[websocket]:
            return
        await websocket.send(json.dumps(data))
        self.websockets[websocket].append(data)
        self.websockets[websocket] = (
            self.websockets[websocket][0-self.keep_items:]
        )

    def clean_websockets(self):
        for websocket in list(self.websockets):
            if websocket.state != 1:
                del self.websockets[websocket]

    def assert_operation_time(self):
        if not self.external:
            return
        min_, max_ = self.external_operation_time
        min_hour, min_minute = min_.split(':')
        max_hour, max_minute = max_.split(':')
        now = datetime.now()
        if now < datetime(
            now.year, now.month, now.day, int(min_hour), int(min_minute)
        ):
            raise RuntimeError('Operation time not reached')
        if now > datetime(
            now.year, now.month, now.day, int(max_hour), int(max_minute)
        ):
            raise RuntimeError('Operation time not reached')

    async def prepare_send(self, result):
        if result not in self.history:
            self.history.append(result)
            self.save_to_influx(result)
            log.info(
                f'{self.type_} fetched new data, sending to '
                f'{len(self.websockets)} clients.'
            )
            for websocket in list(self.websockets):
                await self.send(websocket, result)
        else:
            log.info(
                f'{self.type_} fetched existing data, not sending '
                f'to {len(self.websockets)} clients.'
            )

    def save_to_influx(self, result):
        if not bool(int(self.config.get('FEATURE-influxdb', 'enabled'))):
            return
        db = self.config.get('FEATURE-influxdb', 'db')
        host = self.config.get('FEATURE-influxdb', 'host')
        port = int(self.config.get('FEATURE-influxdb', 'port'))
        ssl = False
        timeout = int(self.config.get('FEATURE-influxdb', 'timeout'))
        user = self.config.get('FEATURE-influxdb', 'user')
        password = self.config.get('FEATURE-influxdb', 'password')

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
            log.error(
                "InfluxDB:  Connect Error to '%s' @ '%s'(%s)" % (
                    str(user), host, db)
            )
            log.error(format(e))
            return
        except Exception as e:
            log.error(
                "InfluxDB: Error while connecting to '%s' @ '%s'(%s)" % (
                    str(user), host, db)
            )
            log.error(e)
            return

        influx_data = {}
        influx_data['measurement'] = self.type_
        influx_data['time'] = datetime.datetime.now()
        influx_data['tags'] = {}
        influx_data['fields'] = result

        points = [influx_data]
        try:
            influx.write_points(points, time_precision='s', protocol='json')
        except InfluxDBClientError as e:
            log.error('InfluxDBError: %s' % (format(e)))
            log.error(
                "InfluxDB failed data:" +
                format(time.strftime("%H:%M:%S", time.localtime(
                    influx_data['time']))
                ),
                format(points)
            )
        else:
            log.info("InfluxDB: new data published %s:%s" % (
                format(time.strftime(
                    "%H:%M:%S", time.localtime(influx_data['time']))
                ),
                format(points))
            )

    async def run(self, once=False):
        while True:
            self.clean_websockets()
            try:
                self.assert_operation_time()
                result = self.data
            except Exception as e:
                log.error(f'Exception while fetching {self.type_} data: {e}')
            else:
                if result:
                    result['DeviceClass'] = self.type_
                    await self.prepare_send(result)
            finally:
                if once:
                    return
                await asyncio.sleep(self.sleep_time)
