import os
import socket
import uuid
import hashlib
import time
import random
import sys
from functools import lru_cache
from configparser import ConfigParser


class Host:
    """
    获取本机IP/HOSTNAME
    >>> Host().host_ip()
    >>> 172.25.4.68
    >>> Host.host_ip()
    >>> 172.25.4.68
    """
    @staticmethod
    @lru_cache()
    def host_ip():
        """
        查询本机ip地址
        """
        ip = None
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
            return ip

    @staticmethod
    @lru_cache()
    def host_name():
        """
        查询本机hostname
        """
        name = None
        try:
            if socket.gethostname().find('.') >= 0:
                name = socket.gethostname()
            else:
                name = socket.gethostbyaddr(socket.gethostname())[0]
        finally:
            return name


class Environ:
    """
    设置/读取环境变量
    >>> env = Environ()
    >>> env.PYTHON_ENV = 'PRO'
    >>> env.PYTHON_ENV
    >>> 'PRO'
    >>> env.PYTHON_ENV_NEW
    >>> None
    """
    def __setattr__(self, env, value):
        os.environ[env] = value

    def __getattr__(self, env):
        return os.environ.get(env, None)


def get_ini_path(filename):
    """
    获取配置文件路径
    """
    if not filename:
        raise Exception('filename can not be empty')
    if not filename.endswith('ini'):
        filename = '{}.ini'.format(filename)
    env = Environ().env
    path = os.path.join('conf', env, filename)
    if not os.path.exists(path):
        raise Exception('can not find file <{}> from conf'.format(filename))
    return path


def get_conf(filename, section=None, key=None):
    """
    解析配置文件内容（返回结果为dict）
    """
    conf = get_ini_path(filename)
    cfg = ConfigParser()
    cfg.read(conf)
    sections = cfg.sections()
    mapper = {}
    for s in sections:
        kvs = cfg.items(s)
        m = {
            kv[0]: kv[1] for kv in kvs
        }
        mapper[s] = m
    if section:
        mapper = mapper.get(section, {})
        if key:
            return mapper.get(key)
        return mapper
    return mapper


def gen_uuid():
    """
    生成UUID
    """
    _uuid = str(uuid.uuid1())
    return _uuid.replace('-', '')


def md5(string):
    """
    md5加密
    """
    m = hashlib.md5()
    m.update(string.encode('utf-8'))
    return m.hexdigest()


def gen_unique_id():
    s = str(time.time() * 100000)
    _uuid = gen_uuid()
    r = str(random.random())
    _str = '{}#{}#{}'.format(s, _uuid, r)
    return md5(_str)


def dict2obj(mapper: dict, recur=False) -> object:
    """
    字典转对象 - 支持多层嵌套
    """
    class Obj:
        pass

    def traverse(mp, oj):
        if not isinstance(mp, dict):
            return oj
        for k, v in mp.items():
            if recur:
                if isinstance(v, dict):
                    setattr(oj, k, traverse(v, oj))
                else:
                    setattr(oj, k, v)
            else:
                setattr(oj, k, v)
        return oj

    return traverse(mapper, Obj)


def get_trace_id_from_stack():
    """
    通过调用栈信息获取trace_id
    最多追溯100层
    """
    max_back_depth, idx = 100, 0
    trace_id = None
    f_back = sys._getframe().f_back
    while idx < max_back_depth:
        if not f_back: break
        local = f_back.f_locals
        if not local: break
        _kwargs = local.get('kwargs')
        kwargs = _kwargs if type(_kwargs) is dict else {}
        trace_id = local.get('__unique_trace_id__') or kwargs.get('__unique_trace_id__')
        if trace_id is not None:
            trace_id = trace_id
            break
        f_back = f_back.f_back
        idx += 1
    return trace_id
