import json
import websockets.exceptions
import asyncio
import requests


class Client:

    corona_url = 'https://api.corona-zahlen.org/districts/15091'
    websockets = None

    def __init__(self, config):
        self.websockets = []

    def register(self, websocket):
        self.websockets.append(websocket)

    async def run(self):
        while True:
            try:
                result = requests.get(self.corona_url).json()
            except Exception:
                pass
            else:
                result['DeviceClass'] = 'Corona'
                for websocket in self.websockets:
                    try:
                        await websocket.send(json.dumps([result]))
                    except websockets.exceptions.ConnectionClosedOK:
                        self.websockets.remove(websocket)
            await asyncio.sleep(30)
