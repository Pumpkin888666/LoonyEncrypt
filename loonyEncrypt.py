"""
Title : loonyEncrypt - 神人加密
Description : 顾名思义，神人加密，加密出来的东西很神。
Author : Pumpkin888666
Email : aswdfgyhj@163.com
"""
import random
import re

default_key_map = {
    "a": 1,
    "b": 2,
    "c": 3,
    "d": 4,
    "e": 5,
    "f": 6,
    "g": 7,
    "h": 8,
    "i": 9,
    "j": 10,
    "k": 11,
    "l": 12,
    "m": 13,
    "n": 14,
    "o": 15,
    "p": 16,
    "q": 17,
    "r": 18,
    "s": 19,
    "t": 20,
    "u": 21,
    "v": 22,
    "w": 23,
    "x": 24,
    "y": 25,
    "z": 26,
    "1": 27,
    "2": 28,
    "3": 29,
    "4": 30,
    "5": 31,
    "6": 32,
    "7": 33,
    "8": 34,
    "9": 35,
    "0": 36,
    "!": 37,
    "@": 38,
    "#": 39,
    "$": 40,
    "%": 41,
    "^": 42,
    "&": 43,
    "*": 44,
}

"""
Key Words:
< > . ( ) / + -

< 表示计算结果加到向前偏移1个对象
<< 表示计算结果加到向前偏移2个对象
...
> 同理

+ 表示加
- 表示减
. 表示乘
/ 表示除

Don't use this words as key map
"""


def s_calculate(value,key_map):
    result = re.split(r"([<>])", value)
    obj = []
    turn = False
    point = 0
    for k, i in enumerate(result):
        if i == "":
            continue
        if i == "<" or i == ">":
            if turn:
                turn = False
                point = point + 1
        else:
            if not turn:
                turn = True
                point = point + 1
        if len(obj) - 1 == point:
            obj[point] = obj[point] + i
        else:
            obj.append(i)
    if len(obj) % 2 != 0:
        raise Exception("原文错误")
    calc = []
    for o in range(1, int(len(obj) / 2) + 1):
        p1 = obj[o * 2 - 2]
        p2 = obj[o * 2 - 1]
        index = o
        if "<" not in p1 or ">" not in p1:
            raise Exception("取p1错误")
        for i in p1:
            if i == "<":
                index -= 1
            elif i == ">":
                index += 1
            else:
                raise Exception("错误的p1")
        if index < 0:
            continue
        if index > len(calc) - 1:
            for _ in range(0,index - len(calc) + 1):
                calc.append(0)
        cal = 0
        for i in p2:
            if i in key_map:
                cal = cal + key_map[i]
        calc[index] += cal
    return calc


def s_encrypt(value, _random=5, iv=0, key_map=None):
    """
    加密函数入口
    :param value:原文。string。
    :param _random:每个文字的最小随机加密次数（在random ~ random * （2~5） 基础上）。int。
    :param iv:密码表偏移量。int。
    :param key_map:密码表。
    :return:
    """
    if key_map is None:
        key_map = default_key_map
    for k, v in key_map.items():
        key_map[k] = v + iv
    if len(value) == 0:
        return value
    ord_codes = []
    for i in value:
        ord_codes.append(ord(i))

    def check(t):
        calc = s_calculate(t,key_map)
        checkout = []
        for i in range(len(calc)):
            checkout.append((calc[i],ord_codes[i]))
        return checkout

    def random_decline(t, g, e):
        pass

    def random_plus(t, g, e):
        pass

    def random_multiply(t, g, e):
        pass

    def random_divide(t, g, e):
        pass

    encrypt_value = ""
    funcs = [random_decline, random_plus, random_multiply, random_divide]
    for i in range(0, len(ord_codes)):
        code = ord_codes[i]
        random.shuffle(funcs)
        for _ in range(_random, _random * random.randint(2, 5)):
            r = check(encrypt_value)
            random.choice(funcs)(encrypt_value, r, False)
        r = check(encrypt_value)
        random.shuffle(funcs)
        random.choice(funcs)(encrypt_value, r, True)


def s_decrypt(value, key_map, ):
    if key_map is None:
        key_map = default_key_map
