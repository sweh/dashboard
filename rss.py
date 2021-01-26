import json
import websockets.exceptions
import asyncio
from rss_parser import Parser
import requests


class Client:

    rss_url = 'https://www.tagesschau.de/xml/rss2/'
    history = None
    websockets = None

    def parse_feed(self):
        xml = requests.get(self.rss_url)
        parser = Parser(xml=xml.content, limit=5)
        feed = parser.parse()
        result = {}
        feed = feed.feed[:]
        feed.reverse()
        for item in feed:
            result['title'] = item.title
            result['description'] = item.description
            result['link'] = item.link
            result['DeviceClass'] = 'RSS'
            if result not in self.history:
                return result

    def __init__(self, config):
        self.config = config
        self.history = []
        self.websockets = []

    async def register(self, websocket):
        self.websockets.append(websocket)
        if self.history:
            await websocket.send(json.dumps([self.history[-1]]))

    async def run(self):
        while True:
            try:
                result = self.parse_feed()
            except Exception:
                pass
            else:
                self.history.append(result)
                self.history = self.history[-3:]
                print(result)
                for websocket in self.websockets:
                    try:
                        await websocket.send(json.dumps([result]))
                    except websockets.exceptions.ConnectionClosedOK:
                        self.websockets.remove(websocket)
            await asyncio.sleep(30)