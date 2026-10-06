"""
Title : loonyEncrypt - 神人加密
Description : 顾名思义，神人加密，加密出来的东西很神。
Author : Pumpkin888666
Email : aswdfgyhj@163.com
"""
import random
import re
import math

default_key_map = {
    "a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7, "h": 8,
    "i": 9, "j": 10, "k": 11, "l": 12, "m": 13, "n": 14, "o": 15,
    "p": 16, "q": 17, "r": 18, "s": 19, "t": 20, "u": 21, "v": 22,
    "w": 23, "x": 24, "y": 25, "z": 26,
    "1": 27, "2": 28, "3": 29, "4": 30, "5": 31, "6": 32, "7": 33,
    "8": 34, "9": 35, "0": 36,
    "!": 37, "@": 38, "#": 39, "$": 40, "%": 41, "^": 42, "&": 43, "*": 44,
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
( 表示加上后面块的平方
) 表示减去后面块的平方

Don't use this words as key map
"""

OPERATORS = set("+-./()")


def evaluate_suffix(suffix, key_map):
    """求值后缀表达式。支持 + - . / ( ) 运算符。"""
    if not suffix:
        return 0
    parts = [p for p in re.split(r"([+\-./()])", suffix) if p != ""]
    if not parts:
        return 0
    if parts[0] in OPERATORS:
        parts = ["0"] + parts

    def block_value(s):
        v = 0
        for ch in s:
            v += key_map.get(ch, 0)
        return v

    result = block_value(parts[0])
    i = 1
    while i + 1 < len(parts):
        op = parts[i]
        operand = block_value(parts[i + 1])
        if op == '+':
            result += operand
        elif op == '-':
            result -= operand
        elif op == '.':
            result *= operand
        elif op == '/':
            if operand != 0:
                result //= operand
        elif op == '(':
            result += operand * operand
        elif op == ')':
            result -= operand * operand
        i += 2
    return result


def s_calculate(value, key_map):
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
            for _ in range(0, index - len(calc) + 1):
                calc.append(0)
        cal = evaluate_suffix(p2, key_map)
        calc[index] += cal
    return calc


# ---------- 后缀生成工具 ----------

def _make_block(v, rev_map):
    """生成字符块，值之和恰为 v。

    均匀随机选值，让字符种类尽可能丰富。
    """
    if v <= 0:
        return ""
    values = list(rev_map.keys())
    parts = []
    remaining = v
    while remaining > 0:
        candidates = [x for x in values if x <= remaining]
        if not candidates:
            break
        chosen = random.choice(candidates)          # 均匀随机，不偏向小值
        parts.append(random.choice(rev_map[chosen]))
        remaining -= chosen
    random.shuffle(parts)
    return ''.join(parts)


def _make_noise(rev_map, level):
    """生成不改变值的噪声后缀。

    用 +X-X 或 .X/X，其中 X 是随机字符块。
    """
    if level <= 0 or not rev_map:
        return ""
    values = list(rev_map.keys())
    out = []
    for _ in range(random.randint(0, level * 2)):
        v = random.choice(values)
        ch = random.choice(rev_map[v])
        if random.random() < 0.5:
            out.append('+' + ch + '-' + ch)         # 加 X 再减 X
        else:
            out.append('.' + ch + '/' + ch)         # 乘 X 再除 X
    return ''.join(out)


def _make_value_expr(v, rev_map, noise_level=0):
    """生成求值为 v 的表达式，风格随机。"""
    if v <= 0:
        # 兜底
        return random.choice(list(rev_map.values()))[0]

    styles = ['block', 'square', 'multiply', 'divide', 'mix', 'mix']
    style = random.choice(styles)

    if v < 10:
        expr = _make_block(v, rev_map)
    elif style == 'square':
        B = int(math.isqrt(v))
        A = v - B * B
        if A == 0:
            b_blk = _make_block(B, rev_map)
            expr = b_blk + '.' + b_blk
        else:
            expr = _make_block(A, rev_map) + '(' + _make_block(B, rev_map)
    elif style == 'multiply':
        factors = [f for f in range(2, int(v ** 0.5) + 1) if v % f == 0]
        if factors:
            a = random.choice(factors)
            b = v // a
            expr = _make_block(a, rev_map) + '.' + _make_block(b, rev_map)
        else:
            expr = _make_block(v, rev_map)
    elif style == 'divide':
        k = random.randint(2, 5)
        expr = _make_block(v * k, rev_map) + '/' + _make_block(k, rev_map)
    elif style == 'mix':
        if v >= 4:
            a = random.randint(1, v - 1)
            b = v - a
            expr = _make_block(a, rev_map) + '+' + _make_block(b, rev_map)
        else:
            expr = _make_block(v, rev_map)
    else:
        expr = _make_block(v, rev_map)

    expr += _make_noise(rev_map, noise_level)
    return expr


def _make_prefix(net_offset):
    """生成前缀，净偏移 = net_offset，且同时含 < 和 >。"""
    if net_offset >= 0:
        return ">" * net_offset + "<>"
    else:
        return "<" * (-net_offset) + "><"


def _random_split(total, n):
    """把 total 随机拆成 n 个正整数，和等于 total。"""
    if n <= 1:
        return [total]
    if total < n:
        n = total
    cuts = sorted(random.sample(range(1, total), n - 1))
    parts = []
    prev = 0
    for c in cuts:
        parts.append(c - prev)
        prev = c
    parts.append(total - prev)
    return parts


def s_encrypt(value, _random=5, iv=0, key_map=None, expand=True):
    """
    加密函数入口
    :param value: 原文。string。
    :param _random: 随机强度。expand=True 时控制每字符的组数上限。int。
    :param iv: 密码表偏移量。int。
    :param key_map: 密码表。
    :param expand: 是否让密文膨胀（多组拆分 + 噪声）。bool。
    :return: 密文
    """
    if key_map is None:
        key_map = dict(default_key_map)
    else:
        key_map = dict(key_map)
    for k in list(key_map.keys()):
        key_map[k] = key_map[k] + iv

    if len(value) == 0:
        return value

    ord_codes = [ord(i) for i in value]

    rev_map = {}
    for k, v in key_map.items():
        rev_map.setdefault(v, []).append(k)

    result = []
    group_count = 0

    for i, T in enumerate(ord_codes):
        if expand:
            n_max = max(1, _random * 3)
            n = random.randint(1, n_max)
            if n > T:
                n = T
            parts = _random_split(T, n) if n > 1 else [T]
        else:
            parts = [T]

        for v in parts:
            if v <= 0:
                continue
            noise = _random if expand else 1
            expr = _make_value_expr(v, rev_map, noise_level=noise)
            next_group = group_count + 1
            net_offset = i - next_group
            prefix = _make_prefix(net_offset)
            result.append(prefix + expr)
            group_count += 1

    return ''.join(result)


def s_decrypt(value, key_map=None, iv=0):
    """
    解密函数入口
    :param value: 密文。string。
    :param key_map: 密码表。
    :param iv: 密码表偏移量。int。
    :return: 原文
    """
    if key_map is None:
        key_map = dict(default_key_map)
    else:
        key_map = dict(key_map)
    for k in list(key_map.keys()):
        key_map[k] = key_map[k] + iv

    calc = s_calculate(value, key_map)
    return "".join(chr(c) for c in calc if c > 0)


# ---------- 测试 ----------
if __name__ == "__main__":
    import time
    print("52pj - Pumpkin888666")
    original = "你好世界"

    for expand in [False, True]:
        for r in [1, 3, 6]:
            t0 = time.time()
            enc = s_encrypt(original, _random=r, expand=expand)
            t1 = time.time()
            dec = s_decrypt(enc)
            t2 = time.time()
            print(f"expand={expand}  _random={r}  长度={len(enc):4d}  "
                  f" 正确={dec == original}")
            print(f"  密文: {enc}")
        print("-" * 70)