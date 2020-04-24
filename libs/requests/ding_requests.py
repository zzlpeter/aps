from . import BaseServer, JsonField, QueryField
from libs.tomlread import ConfEntity

ding_ding_dict = ConfEntity().common['ding']


class DingServer(BaseServer):
    __HOST__ = ding_ding_dict['ding']
    TIMEOUT = 5


class DingDingAlarm(DingServer):
    """
    钉钉报警
    """
    URL = '/robot/send'
    METHOD = 'POST'
    access_token = QueryField(default='fdbf4738cb4dc9d0094e0b476853c39b666150cefdc9e52c7066f3eddb6c5f75')
    msgtype = JsonField(default='text')
    text = JsonField(required=True)
