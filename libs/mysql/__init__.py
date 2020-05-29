"""
MySQL连接池管理
"""
import peewee_async
from playhouse.shortcuts import ReconnectMixin

from libs.tomlread import ConfEntity
from libs.decorators import singleton
from libs.utils.other import dict2obj


__all__ = [
    'MysqlPools',
]


class RetryMySQLDatabase(ReconnectMixin, peewee_async.PooledMySQLDatabase):
    @staticmethod
    def get_db_instance(db, **conf):
        if not RetryMySQLDatabase._instance:
            RetryMySQLDatabase._instance = RetryMySQLDatabase(db, **conf)
        return RetryMySQLDatabase._instance


@singleton
class Mysql:
    mysql_pools = {}

    def create_pool(self):
        _mysql_pools = {}
        mysql_conf = ConfEntity().mysql
        for alias, cnf in mysql_conf.items():
            conf = cnf.copy()
            db = conf.pop('db')
            # 自动重新建立链接
            db_conn = RetryMySQLDatabase(db, **conf)
            manager = peewee_async.Manager(db_conn)
            # 每个链接对象有两个属性：.db_conn  .manager
            _mysql_pools[alias] = dict2obj(dict(db_conn=db_conn, manager=manager))
        self.mysql_pools = _mysql_pools

    @property
    def pools(self):
        if not self.mysql_pools:
            self.create_pool()
        return self.mysql_pools


@singleton
class MysqlWrapper:
    pools = Mysql().pools

    def __getattr__(self, key):
        return self.pools.get(key)


MysqlPools = MysqlWrapper()


"""
参照 models/task
使用peewee orm
防止SQL注入、建议通过orm操作
"""