import xml.etree.ElementTree as ET
import requests
from baseclient import BaseClient


class Client(BaseClient):

    type_ = 'Helios'

    def grab_helios_data(self):
        payload = {
            "v00003": "de",
            "v01306": "v01306",
            "v00001": "v00001",
            "v00402": self.config.get("HELIOS", 'password'),
            "but0": "Anmelden",
        }

        session_requests = requests.session()

        result = session_requests.post(
            'http://10.0.1.64/info.htm',
            data=payload,
            headers=dict(referer='http://10.0.1.64')
        )

        headers = {
            "Host": "10.0.1.64",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:65.0)"
                " Gecko/20100101 Firefox/65.0"
            ),
            "Accept": "*/*",
            "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate",
            "Referer": "http://10.0.1.64/anzeig.htm",
            "Referrer-Policy": "no-referrer-when-downgrade",
            "Content-Type": "text/plain;charset=UTF-8",
            "Content-Length": "20",
            "Connection": "keep-alive"}

        result = session_requests.post(
            'http://10.0.1.64/data/werte8.xml',
            headers=headers,
            data="xml=/data/werte8.xml",
        )

        data = dict()
        key = None
        for id, child in enumerate(ET.fromstring(result.text)):
            if id == 0:
                continue
            if key is None:
                key = child
            else:
                data[key.text] = child.text
                key = None
        return data

    @property
    def data(self):
        heliosdata = self.grab_helios_data()
        result = dict(
            stufe=heliosdata['v00102'],
            stufe_tendency='right',
            percent=heliosdata['v00103'],
            percent_tendency='right',
            aussenluft=float(heliosdata['v00104']),
            aussenluft_tendency='right',
            zuluft=float(heliosdata['v00105']),
            zuluft_tendency='right',
            fortluft=float(heliosdata['v00106']),
            fortluft_tendency='right',
            abluft=float(heliosdata['v00107']),
            abluft_tendency='right',
            abluft_feuchte=heliosdata['v02136'],
            abluft_feuchte_tendency='right',
        )
        if self.history:
            old_value = self.history[-1]
            for key in (
                'stufe', 'percent', 'aussenluft', 'zuluft',
                'fortluft', 'abluft', 'abluft_feuchte'
            ):
                if old_value[key] > result[key]:
                    result[key + '_tendency'] = 'down'
                elif old_value[key] < result[key]:
                    result[key + '_tendency'] = 'up'
        return result
