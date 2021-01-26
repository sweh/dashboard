import asyncio
import websockets
import argparse
from sma_daemon import MyDaemon
from openweather import Client as OpenWeatherClient
from corona import Client as CoronaClient
from helios import Client as HeliosClient
from rss import Client as RSSClient


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
    openweatherclient = OpenWeatherClient(smadaemon.config)
    coronaclient = CoronaClient(smadaemon.config)
    heliosclient = HeliosClient(smadaemon.config)
    rssclient = RSSClient(smadaemon.config)

    async def server(websocket, path):
        smadaemon.register(websocket)
        openweatherclient.register(websocket)
        coronaclient.register(websocket)
        heliosclient.register(websocket)
        rssclient.register(websocket)
        while True:
            # Get received data from websocket
            data = await websocket.recv()
            print(data)
            await asyncio.sleep(1)

    tasks = [
        websockets.serve(server, "localhost", 6790),
        smadaemon.run(),
        openweatherclient.run(),
        coronaclient.run(),
        heliosclient.run(),
        rssclient.run(),
    ]

    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))
    asyncio.get_event_loop().run_forever()
