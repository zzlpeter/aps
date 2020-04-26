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
    access_token = QueryField(required=True)
    msgtype = JsonField(default='text')
    text = JsonField(required=True)
