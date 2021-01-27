from rss_parser import Parser
from baseclient import BaseClient
import requests


class Client(BaseClient):

    rss_url = 'https://www.tagesschau.de/xml/rss2/'
    type_ = 'RSS'

    @property
    def data(self):
        xml = requests.get(self.rss_url)
        parser = Parser(xml=xml.content, limit=1)
        feed = parser.parse()
        item = feed.feed[0]
        return dict(
            title=item.title,
            description=item.description,
            link=item.link
        )
