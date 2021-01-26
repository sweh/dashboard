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
        parser = Parser(xml=xml.content, limit=2)
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

    def register(self, websocket):
        self.websockets.append(websocket)

    async def run(self):
        while True:
            try:
                result = self.parse_feed()
            except Exception:
                pass
            else:
                self.history.append(result)
                for websocket in self.websockets:
                    try:
                        await websocket.send(json.dumps([result]))
                    except websockets.exceptions.ConnectionClosedOK:
                        self.websockets.remove(websocket)
            await asyncio.sleep(30)
