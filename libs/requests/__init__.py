import json
import traceback
from itertools import chain
import urllib.parse

import aiohttp
import requests

from libs.logger import LoggerPool

logger = LoggerPool.root
SPECIAL_ATTRS = ('__query__', '__data__', '__json__', '__path1__')


class SpecialEmpty(object):
    pass


class Field(object):
    def __init__(self, default, required):
        self.default = default
        self.required = required

    def __str__(self):
        return '<%s:%s>' % (self.__class__.__name__, self.default)


class DataField(Field):
    def __init__(self, default=None, required=False):
        super(DataField, self).__init__(default, required)


class QueryField(Field):
    def __init__(self, default=None, required=False):
        super(QueryField, self).__init__(default, required)


class JsonField(Field):
    def __init__(self, default=None, required=False):
        super(JsonField, self).__init__(default, required)


class PathField(Field):
    def __init__(self, default=None, required=False):
        super(PathField, self).__init__(default, required)


class RequestMetaClass(type):
    def __new__(cls, name, bases, attrs):
        # parameters should be classified as below four types
        # query_mapper    ->    host/path?query1=val1&query2=val2
        # data_mapper     ->    post parameters with formData
        # json_mapper     ->    post parameters with application/json
        # path_mapper     ->    fill parameter with path Eg: http://www.example.com/test/{column}/{id}
        query_mapper = {}
        data_mapper = {}
        json_mapper = {}
        path_mapper = {}

        # to get parents's parameters
        parent_attrs = {}
        for base in bases:
            if issubclass(base, SpecialEmpty):
                for attr in SPECIAL_ATTRS:
                    attr_val = getattr(base, attr, None)
                    if type(attr_val) is dict:
                        parent_attrs.update(attr_val)

        # child's property can overwrite parents's
        # pls do not change this !!!
        parent_attrs.update(attrs)
        attrs = parent_attrs
        for k, v in attrs.items():
            if isinstance(v, DataField):
                data_mapper[k] = v
            if isinstance(v, QueryField):
                query_mapper[k] = v
            if isinstance(v, JsonField):
                json_mapper[k] = v
            if isinstance(v, PathField):
                path_mapper[k] = v

        # clear class property to protect instance property
        for k in chain(query_mapper.keys(), data_mapper.keys(), json_mapper.keys(), path_mapper.keys()):
            attrs.pop(k, None)

        attrs['__query__'] = query_mapper
        attrs['__data__'] = data_mapper
        attrs['__json__'] = json_mapper
        attrs['__path1__'] = path_mapper

        return type.__new__(cls, name, bases, attrs)


class BaseServer(SpecialEmpty, dict, object, metaclass=RequestMetaClass):
    # __metaclass__ = RequestMetaClass

    def __init__(self, **kwargs):
        super(BaseServer, self).__init__(**kwargs)

    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError('"BaseServer" has no attribute "%s"' % key)

    def __getitem__(self, item):
        return self.get(item, None)

    def _set_headers(self):
        self._header = getattr(self, 'HEADERS', {})

    def _set_timeout(self):
        self._timeout = getattr(self, 'TIMEOUT', 5)

    def _set_request_url(self):
        self._url = urllib.parse.urljoin(self.__HOST__, self.URL)
        if self._path1:
            self._url = self._url.format(**self._path1)

    def _set_method(self):
        self._method = self.METHOD.lower()

    def new_server(self):
        self._data, self._query, self._json, self._path1 = {}, {}, {}, {}
        for attr in SPECIAL_ATTRS:
            for k, v in getattr(self, attr, {}).items():
                vv = self[k] or v.default
                if v.required and vv is None:
                    raise AttributeError('Class %s with %s %s is required, found the given value is %s' %
                                         (self.__class__.__name__, v.__class__.__name__, k, vv))
                self['_{}'.format(attr.strip('_'))][k] = vv
        self._set_headers()
        self._set_timeout()
        self._set_request_url()
        self._set_method()
        self._prepare_request_args()
        return self

    def _prepare_request_args(self):
        req_map = {}
        if self._query:
            req_map['params'] = self._query
        if self._data:
            req_map['data'] = self._data
        if self._json:
            req_map['json'] = self._json
        self._req_map = req_map

    def fetch(self):
        response = requests.request(self._method, self._url, headers=self._header,
                                    timeout=self._timeout, **self._req_map)
        self._fetch_url = response.url
        self._response = response.content
        return self

    async def async_fetch(self):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            handle = getattr(session, self._method)
            timeout = aiohttp.ClientTimeout(total=self._timeout)
            async with handle(url=self._url, timeout=timeout, headers=self._header, **self._req_map) as response:
                self._fetch_url = response.url
                self._response = await response.text()
            return self

    def json(self, safe=True):
        try:
            return json.loads(self._response)
        except Exception as e:
            logger.error({'panic_keyword': '_unserialize_err', 'err': traceback.format_exc(),
                          'url': self._url, 'fetch_url': self._fetch_url, 'data': self._data,
                          'query': self._query, 'json': self._json, 'rsp': self._response})
            if safe:
                return {}
            raise e

    def content(self):
        return self._response


"""EXAMPLE
from . import BaseServer, DataField, QueryField, JsonField

class BackendServer(BaseServer):
    __HOST__ = 'http://www.test.com'
    TIMEOUT = 5  # 默认为5s

class ReqTest(BackendServer):
    URL = '/test/api/get/{path_score}'
    METHOD = 'get'
    query_name = QueryField('')
    query_age = QueryField(12, required=True)
    data_sex = DataField()
    json_weight = JsonField()
    path_score = PathField()

if __name__ == '__main__':
    r = ReqTest(name='name1').new_server()

    resp_sync = r.fetch()
    resp_async = await r.async_fetch()

    resp_with_content = resp_sync.content()
    resp_with_content = resp_async.content()

    resp_with_json = resp_sync.json()
    resp_with_json = resp_async.json()
"""
