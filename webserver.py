import asyncio
import json
import websockets
import argparse
from sma_daemon import MyDaemon
from clients.pv import Client as PVClient
from clients.openweather import Client as OpenWeatherClient
from clients.corona import Client as CoronaClient
from clients.helios import Client as HeliosClient
# from clients.rss import Client as RSSClient
from clients.hue import Client as HueClient
from clients.motd import Client as MotdClient


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
    pvclient = PVClient(smadaemon)
    openweatherclient = OpenWeatherClient(smadaemon.config)
    coronaclient = CoronaClient(smadaemon.config)
    heliosclient = HeliosClient(smadaemon.config)
    # rssclient = RSSClient(smadaemon.config)
    motdclient = MotdClient(smadaemon.config)
    hueclient = HueClient(smadaemon.config)

    async def server(websocket, path):
        await pvclient.register(websocket)
        await openweatherclient.register(websocket)
        await coronaclient.register(websocket)
        await heliosclient.register(websocket)
        # await rssclient.register(websocket)
        await hueclient.register(websocket)
        await motdclient.register(websocket)
        while True:
            # Get received data from websocket
            data = await websocket.recv()
            if data:
                data = json.loads(data)
                if 'helios_stufe' in data:
                    try:
                        heliosclient.set_stufe(data['helios_stufe'])
                    except Exception:
                        pass
                elif 'hue' in data:
                    try:
                        hueclient.set_status(data['hue'])
                    except Exception:
                        pass
            await asyncio.sleep(1)

    tasks = [
        websockets.serve(server, "localhost", 6790),
        pvclient.run(),
        openweatherclient.run(),
        coronaclient.run(),
        heliosclient.run(),
        # rssclient.run(),
        hueclient.run(),
        motdclient.run(),
    ]

    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))
    asyncio.get_event_loop().run_forever()
