import asyncio
import websockets
import argparse
from sma_daemon import MyDaemon


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

    async def server(websocket, path):
        smadaemon.register(websocket)
        while True:
            # Get received data from websocket
            data = await websocket.recv()
            print(data)
            await asyncio.sleep(1)

    start_dashboard = websockets.serve(server, "0.0.0.0", 6789)

    tasks = [
        smadaemon.run(),
        websockets.serve(server, "0.0.0.0", 6789)
    ]

    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))
    asyncio.get_event_loop().run_forever()
