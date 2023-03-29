import datetime
import random
import time
import typing
from flask import Request


def get_unix_time_tuple(
    date=datetime.datetime.now(), millisecond: bool = False
) -> str:
    """ get time tuple
    get unix time tuple, default `date` is current time
    Args:
        date: datetime, default is datetime.datetime.now()
        millisecond: if True, Use random three digits instead of milliseconds, default id False 
    Return:
        a str type value, return unix time of incoming time
    """
    time_tuple = time.mktime(date.timetuple())
    time_tuple = round(time_tuple * 1000) if millisecond else time_tuple
    second = str(int(time_tuple))
    return second


def parse_params(request: Request) -> typing.Dict[str, typing.Any]:
    """  从一个Request实例中解析params参数
    Args:
        request: flask.request 实例对象
    Return: 一个解析过的字典对象，如果没有解析出，则返回一个空的字典对象
    """
    params = request.values or request.get_json() or {}
    return dict(params)


def get_random_num(digit: int = 6) -> str:
    """ get a random num
    get random num 
    Args:
        digit: digit of the random num, limit (1, 32)
    Return:
        return Generated random num
    """
    if digit is None:
        digit = 1
    digit = min(max(digit, 1), 32)    # 最大支持32位
    result = ""
    while len(result) < digit:
        append = str(random.randint(1, 9))
        result = result + append
    return result
