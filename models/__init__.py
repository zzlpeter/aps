import json

from peewee import TextField


class JsonField(TextField):
    def db_value(self, value):
        try:
            return json.dumps(value)
        except:
            return value

    def python_value(self, value):
        try:
            return json.loads(value)
        except:
            return value


class ConnectionManager(object):
    @classmethod
    def close(cls):
        db = cls._meta.database
        db.close()

    @classmethod
    def connect(cls):
        db = cls._meta.database
        db.connect(reuse_if_open=True)
