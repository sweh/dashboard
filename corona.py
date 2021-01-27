import requests
from baseclient import BaseClient


class Client(BaseClient):

    corona_url = 'https://api.corona-zahlen.org/districts/15091'
    type_ = 'Corona'

    @property
    def data(self):
        return requests.get(self.corona_url).json()
