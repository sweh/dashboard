from sqlalchemy.orm import sessionmaker, class_mapper
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

    def __init__(self, name, engine, max_items=None):
        self.db_class = getattr(model, name, None)
        self.session = sessionmaker(bind=engine)()
        self.name = f'history_{name}.bin'
        self.max_items = max_items
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
        for item in (
            self.session.query(self.db_class)
            .order_by(self.db_class._timestamp.asc())
            .limit(self.max_items)
        ):
            item = sqlalchemy_encode(item)
            item['DeviceClass'] = self.db_class.__name__
            self._data.append(item)

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
