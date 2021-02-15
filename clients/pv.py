import json
from datetime import datetime
from speedwiredecoder import decode_speedwire
from clients.baseclient import BaseClient


class Client(BaseClient):

    sleep_time = 2
    type_ = 'PV'
    keep_items = 1000

    def __init__(self, smadaemon):
        self.smadaemon = smadaemon
        super(Client, self).__init__(smadaemon.config)
        self.sock = smadaemon.connect_to_socket()
        self.sums = dict()
        self.costs = dict()
        self.costs_per_hour = dict()

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
        if data['consumption'] < 0:
            data['consumption'] = 0 - data['consumption']
        data_file = self.config.get('FEATURE-pvdata', 'output_file')
        if data_file:
            with open(data_file, 'w') as f:
                f.write(json.dumps(data))

    def calculate_sums(self, result):
        fmt = "%Y-%m-%dT%H:%M:%S.%f%z"

        seconds = 1
        if self.history:
            current = datetime.strptime(result['timestamp'], fmt)
            last = datetime.strptime(self.history[-1]['timestamp'], fmt)
            if current.day != last.day:
                self.costs = dict()
                self.sums = dict()
                seconds = 1
            else:
                seconds = current - last
                seconds = float(f'{seconds.seconds}.{seconds.microseconds}')
        for key in (
            'Consumption',
            'AC Power Solar',
            'Power to grid',
            'AC Power Battery',
            'Power from grid'
        ):
            self.sums.setdefault(key, 0)
            self.sums[key] += result[key] / 3600 * seconds

    def calculate_costs(self, result):
        self.costs.setdefault('Power to grid', 0)
        self.costs['Power to grid'] = (
            self.sums['Power to grid'] / 1000 * 0.0877
        )
        self.costs.setdefault('Power from grid', 0)
        self.costs['Power from grid'] = (
            self.sums['Power from grid'] / 1000 * 0.3000
        )
        self.costs.setdefault('Power saving', 0)
        self.costs['Power saving'] = (
            self.sums['Consumption'] - self.sums['Power from grid']
        ) / 1000 * 0.3000

    def calculate_costs_per_hour(self, result):
        self.costs_per_hour.setdefault('Power to grid', 0)
        self.costs_per_hour['Power to grid'] = (
            result['Power to grid'] / 1000 * 0.0877
        )
        self.costs_per_hour.setdefault('Power from grid', 0)
        self.costs_per_hour['Power from grid'] = (
            result['Power from grid'] / 1000 * 0.3000
        )
        self.costs_per_hour.setdefault('Power saving', 0)
        self.costs_per_hour['Power saving'] = (
            result['Consumption'] - result['Power from grid']
        ) / 1000 * 0.3000

    @property
    def data(self):
        result = {}
        emparts = decode_speedwire(self.sock.recv(608))
        for serial in self.smadaemon.serials:
            if serial == format(emparts["serial"]):
                for items in self.run_features(emparts):
                    for item in items:
                        if item['DeviceClass'] == 'Solar Inverter':
                            item['AC Power Solar'] = item['AC Power'] or 0
                            item['Status Solar'] = item['Status']
                        if item['DeviceClass'] == 'Battery Inverter':
                            item['AC Power Battery'] = item['AC Power'] or 0
                        result.update(item)
        result['Power to grid'] = result['Power to grid'] or 0
        result['Consumption'] = (
            result['AC Power Solar'] +
            result['AC Power Battery'] +
            result['Power from grid'] -
            result['Power to grid']
        )
        if result:
            self.save_result_to_file(result)
        self.calculate_sums(result)
        result['sums'] = self.sums
        self.calculate_costs(result)
        result['costs'] = self.costs
        self.calculate_costs_per_hour(result)
        result['costs_per_hour'] = self.costs_per_hour
        return result

    def run_features(self, emparts):
        # running all enabled features
        for feature in self.smadaemon.featurelist:
            result = feature["feature"].run(
                emparts, feature["config"]
            )
            if result:
                yield result
