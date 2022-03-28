from clients.corona import Client as CoronaClient
from clients.helios import Client as HeliosClient
from clients.hue import Client as HueClient
from clients.motd import Client as MotdClient
from clients.openweather import Client as OpenWeatherClient
from clients.pv import Client as PVClient
from clients.pvsums import Client as PVSumsClient
from clients.rss import Client as RSSClient
from clients.tado import Client as TadoClient
from clients.vicare import Client as ViCareClient
from clients.gardena import Client as GardenaClient
from clients.wifi import Client as WifiClient
from sma_daemon import MyDaemon
from sqlalchemy import create_engine
import argparse
import asyncio
import json
import logging
import model
import websockets

logging.basicConfig(level=logging.WARN)
logging.getLogger().setLevel(logging.WARN)
log = logging.getLogger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Dashboard wehrmann.it'
    )
    parser.add_argument(
        '-c',
        dest='config',
        default='/etc/smaemd/config',
        help='Specify the config file. (default: /etc/smaemd/config)',
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    smadaemon = MyDaemon(args.config)
    smadaemon.config.engine = smadaemon.config.get('DB', 'connect')
    if smadaemon.config.engine:
        smadaemon.config.engine = create_engine(smadaemon.config.engine)
        model.Base.metadata.create_all(smadaemon.config.engine)

    hueclient = HueClient(smadaemon.config)
    clients = dict(
        pvclient=PVClient(smadaemon, hueclient),
        pvsumsclient=PVSumsClient(smadaemon.config),
        coronaclient=CoronaClient(smadaemon.config),
        heliosclient=HeliosClient(smadaemon.config),
        # rssclient=RSSClient(smadaemon.config),
        # motdclient=MotdClient(smadaemon.config),
        wificlient=WifiClient(smadaemon.config),
        hueclient=hueclient,
        tadoclient=TadoClient(smadaemon.config),
        vicareclient=ViCareClient(smadaemon.config),
        gardenaclient=GardenaClient(smadaemon.config),
        openweatherclient=OpenWeatherClient(smadaemon.config),
    )

    async def server(websocket, path):
        for client in clients.values():
            if client.enabled:
                await client.register(websocket)

        while True:
            # Get received data from websocket
            data = await websocket.recv()
            if data:
                data = json.loads(data)
                for key, value in data.items():
                    try:
                        await clients[f'{key}client'].set_status(value)
                    except Exception as e:
                        log.error(f'Exception while setting {key}: {e}')
            await asyncio.sleep(1)

    tasks = [
        websockets.serve(
            server,
            smadaemon.config.get("DAEMON", "ipbind"),
            6790
        ),
    ]
    tasks.extend(
        [c.run() for c in clients.values() if c.enabled]
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    loop.run_forever()
