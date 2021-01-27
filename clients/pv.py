import json
from speedwiredecoder import decode_speedwire
from clients.baseclient import BaseClient


class Client(BaseClient):

    sleep_time = 1
    type_ = 'PV'
    keep_items = 100
    data_file = '/tmp/pvdata.txt'

    def __init__(self, smadaemon):
        self.smadaemon = smadaemon
        super(Client, self).__init__(smadaemon.config)
        self.sock = smadaemon.connect_to_socket()

    def save_result_to_file(self, data):
        data = dict(
            panelpower=data['AC Power Solar'] or 0,
            batterypower=0-data['AC Power Battery'] or 0,
            power_from_grid=data['Power from grid'] or 0,
            power_to_grid=data['Power to grid'] or 0
        )
        data['consumption'] = (
                data['panelpower'] + data['batterypower'] +
                data['power_from_grid'] - data['power_to_grid']
        )
        data_file = self.config.get('FEATURE-pvdata', 'output_file')
        if data_file:
            with open(data_file, 'w') as f:
                f.write(json.dumps(data))

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
        if result:
            self.save_result_to_file(result)
        return result

    def run_features(self, emparts):
        # running all enabled features
        for feature in self.smadaemon.featurelist:
            result = feature["feature"].run(
                emparts, feature["config"]
            )
            if result:
                yield result
