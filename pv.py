from speedwiredecoder import decode_speedwire
from baseclient import BaseClient


class Client(BaseClient):

    sleep_time = 1
    type_ = 'PV'

    def __init__(self, smadaemon):
        self.smadaemon = smadaemon
        super(Client, self).__init__(smadaemon.config)
        self.sock = smadaemon.connect_to_socket()

    @property
    def data(self):
        result = {}
        emparts = decode_speedwire(self.sock.recv(608))
        for serial in self.smadaemon.serials:
            if serial == format(emparts["serial"]):
                for items in self.run_features(emparts):
                    for item in items:
                        if item['DeviceClass'] == 'Solar Inverter':
                            item['AC Power Solar'] = item['AC Power']
                            item['Status Solar'] = item['Status']
                        if item['DeviceClass'] == 'Battery Inverter':
                            item['AC Power Battery'] = item['AC Power']
                        result.update(item)
        return result

    def run_features(self, emparts):
        # running all enabled features
        for feature in self.smadaemon.featurelist:
            result = feature["feature"].run(
                emparts, feature["config"]
            )
            if result:
                yield result
