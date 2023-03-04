from sqlalchemy.orm import sessionmaker, class_mapper
import datetime
import decimal
import json
import model
import pickle
import os.path


def sqlalchemy_encode(o):
    columns = [c.key for c in class_mapper(o.__class__).columns]
    result = dict((c, getattr(o, c)) for c in columns)
    for k, v in o.name_mapping.items():
        result[v] = result[k]
    return result


class History:

    name = None
    db_class = None
    session = None

    def __init__(self, name, engine, max_items=None, max_datetime=None):
        self.db_class = getattr(model, name, None)
        self.session = sessionmaker(bind=engine)()
        self.name = f'history_{name}.bin'
        self.max_items = max_items
        self.max_datetime = max_datetime
        self.load()

    def append(self, item):
        self._data.append(item)
        self.save()

    def get(self):
        if self.max_items is None:
            return self._data
        return self._data[0-self.max_items:]

    def load(self):
        if self.db_class:
            self._load_from_db()
        else:
            self._load_pickle()

    def _load_pickle(self):
        if not os.path.exists(self.name):
            self._data = []
        else:
            with open(self.name, 'rb') as f:
                self._data = pickle.load(f)

    def _load_from_db(self):
        self._data = []
        query = self.session.query(self.db_class)
        if self.max_datetime:
            query = query.filter(self.db_class._timestamp >= self.max_datetime)
        query = query.order_by(self.db_class._timestamp.desc())
        if self.max_items:
            query = query.limit(self.max_items)
        for item in query:
            item = sqlalchemy_encode(item)
            item['DeviceClass'] = self.db_class.__name__
            self._data.append(item)
        self._data.reverse()

    def save(self):
        if self.db_class:
            self._save_to_db()
        else:
            self._save_pickle()
        self._data = self._data[0-self.max_items:]

    def _save_pickle(self):
        with open(self.name, 'wb') as f:
            pickle.dump(self._data[0-self.max_items:], f)

    def _save_to_db(self):
        item = self.db_class()
        last = self._data[-1]
        for k, v in last.items():
            setattr(item, k, v)
        for k, v in self.db_class.name_mapping.items():
            setattr(item, k, last[v])
        self.session.add(item)
        item.prepare(self.session)
        self.session.commit()

    def get_last_entry(self):
        try:
            return self.get()[-1]
        except IndexError:
            return

    def __iter__(self):
        return iter(self.get())

    def __contains__(self, item):
        return item in self.get()

    def __getitem__(self, index):
        return self.get()[index]


def datetime_encode(o, request=None):
    return o.isoformat()


def decimal_encode(o, request=None):
    return str(o)


ENCODERS = {model.Base: sqlalchemy_encode,
            datetime.date: datetime_encode,
            datetime.datetime: datetime_encode,
            decimal.Decimal: decimal_encode}


def encode(o):
    for klass, encoder in ENCODERS.items():
        if isinstance(o, klass):
            return encoder(o)
    return json._default_encoder._default_orig(o)


json._default_encoder._default_orig = json._default_encoder.default
json._default_encoder.default = encode
