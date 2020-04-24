import time
from datetime import datetime
import arrow


def datetime_fmt(dt=None, fmt='%Y-%m-%d %H:%M:%S'):
    if isinstance(dt, datetime):
        return dt.strftime(fmt)
    return datetime.now().strftime(fmt)


def now_timestamp():
    """
    获取当前时间戳
    """
    return int(time.time())


def now_millitimestamp():
    """
    获取当前微秒时间戳
    """
    return int(time.time() * 1000)


def datestr2utcdatetime(date_str, fmt='YYYY-MM-DD HH:mm:ss'):
    """
    时间字符串转成 utc datetime
    """
    return arrow.get(date_str, fmt).datetime


def datestr2bjdatetime(date_str, fmt='YYYY-MM-DD HH:mm:ss'):
    """
    时间字符串转成 北京 datetime
    """
    return arrow.get(date_str, fmt).to('Asia/Shanghai').datetime


def datestr2localdatetime(date_str, fmt='YYYY-MM-DD HH:mm:ss'):
    """
    时间字符串转成 本地 datetime
    """
    return arrow.get(date_str, fmt).to('local').datetime


def utcdatetime2bjdatetime(utc_date):
    """
    utc datetime 转为 北京  datetime
    :param utc_date: datetime.datetime(2018, 11, 21, 16, 27, 13, 883211)
    :return: datetime.datetime(2018, 11, 21, 16, 27, 13, 883211)
    """
    utc_arrow = arrow.get(utc_date)
    return utc_arrow.to('Asia/Shanghai').datetime


def utcdatetime2localdatetime(utc_date):
    """
    utc datetime 转为 本地  datetime
    :param utc_date: datetime.datetime(2018, 11, 21, 16, 27, 13, 883211)
    :return: datetime.datetime(2018, 11, 21, 16, 27, 13, 883211)
    """
    utc_arrow = arrow.get(utc_date)
    return utc_arrow.to('local').datetime


def timestamp2bjdatestr(stamp, fmt='%Y-%m-%d %H:%M:%S'):
    """
    时间戳转为北京时间字符串
    :param stamp: 1485937858
    :return:
    """
    arrow_obj = arrow.get(stamp)
    return arrow_obj.to('Asia/Shanghai').datetime.strftime(fmt)


def datetime_shift(dt, **kwargs):
    """
    datetime 偏移量
    :param dt:
    :param kwargs: years=0, months=0, days=0, hours=0, minutes=0, seconds=0, weeks=0
    :return:
    """
    arrow_obj = arrow.get(dt)
    return arrow_obj.shift(**kwargs).datetime


def datetime2timestamp(dt):
    """
    datetime to timestamp
    :param dt:
    :return:
    """
    return arrow.get(dt).timestamp


def timestamp2utcdatetime(stamp):
    """
    timestamp to utc datetime
    :param stamp:
    :return:
    """
    return arrow.get(stamp).to('utc').datetime


def get0timestamp():
    """
    获取当前时间0点时间戳
    :return:
    """
    now = now_timestamp()
    bjdate = timestamp2bjdatestr(now, '%Y-%m-%d')
    return datetime2timestamp(bjdate)
