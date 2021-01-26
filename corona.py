import json
import websockets.exceptions
import asyncio
import requests


class Client:

    corona_url = 'https://api.corona-zahlen.org/districts/15091'
    history = None
    websockets = None

    def __init__(self, config):
        self.history = []
        self.websockets = []

    async def register(self, websocket):
        self.websockets.append(websocket)
        if self.history:
            await websocket.send(json.dumps([self.history[-1]]))

    async def run(self):
        while True:
            try:
                result = requests.get(self.corona_url).json()
            except Exception:
                pass
            else:
                result['DeviceClass'] = 'Corona'
                self.history.append(result)
                self.history = self.history[-10:]
                print(result)
                for websocket in self.websockets:
                    try:
                        await websocket.send(json.dumps([result]))
                    except websockets.exceptions.ConnectionClosedOK:
                        self.websockets.remove(websocket)
            await asyncio.sleep(30)
