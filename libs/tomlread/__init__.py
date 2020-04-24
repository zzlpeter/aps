import os
import toml

from libs.decorators import singleton


def get_conf_path(filename):
    """
    获取配置文件路径
    """
    if not filename:
        raise Exception('filename can not be empty')
    if not filename.endswith('toml'):
        filename = '{}.toml'.format(filename)
    from libs.utils.other import Environ
    env = Environ().APP_ENV or 'local'
    path = os.path.join('conf', env, filename)
    if not os.path.exists(path):
        raise Exception('can not find file <{}> from conf'.format(filename))
    return path


@singleton
class ConfEntity:

    conf = dict()

    @property
    def mysql(self):
        conf = get_conf_path('mysql')
        if 'mysql' not in self.conf:
            with open(conf, encoding='utf-8') as cf:
                self.conf['mysql'] = toml.loads(cf.read())

        return self.conf['mysql']

    @property
    def redis(self):
        conf = get_conf_path('redis')
        if 'redis' not in self.conf:
            with open(conf, encoding='utf-8') as cf:
                self.conf['redis'] = toml.loads(cf.read())

        return self.conf['redis']

    @property
    def common(self):
        conf = get_conf_path('common')
        if 'common' not in self.conf:
            with open(conf, encoding='utf-8') as cf:
                self.conf['common'] = toml.loads(cf.read())

        return self.conf['common']

    @property
    def logger(self):
        conf = get_conf_path('logger')
        if 'logger' not in self.conf:
            with open(conf, encoding='utf-8') as cf:
                self.conf['logger'] = toml.loads(cf.read())

        return self.conf['logger']
