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
