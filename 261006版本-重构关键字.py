"""
Title : loonyEncrypt - 神人加密（括号重定义版）
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


# ============================================================
#                       解密端
# ============================================================

def evaluate_expression(expr, key_map):
    """
    对表达式字符串求值。
    支持的运算符：+ - . /
    从左到右求值，无优先级。
    （( 和 ) 不再是运算符，它们是结构性字符）
    """
    if not expr:
        return 0
    parts = [p for p in re.split(r"([+\-./])", expr) if p != ""]
    if not parts:
        return 0
    if parts[0] in '+-./':
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
        i += 2
    return result


def _parse_groups(cipher):
    """
    把密文解析为 (p1, kind, body) 列表。
    - p1: 一串 '<' 和 '>'
    - kind: 'expr' 或 'paren'
    - body: 表达式字符串（expr）或子密文字符串（paren）
    """
    groups = []
    i = 0
    n = len(cipher)
    while i < n:
        # 收集 p1
        p1_start = i
        while i < n and cipher[i] in '<>':
            i += 1
        if i == p1_start:
            raise Exception(f"位置 {i} 处期望 '<' 或 '>'，得到 {cipher[i]!r}")
        p1 = cipher[p1_start:i]

        if i >= n:
            raise Exception("前缀后缺少内容")

        if cipher[i] == '(':
            # 括号块：匹配到对应的 )
            depth = 0
            j = i
            while j < n:
                if cipher[j] == '(':
                    depth += 1
                elif cipher[j] == ')':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if j >= n:
                raise Exception("括号不匹配")
            inner = cipher[i + 1:j]
            groups.append((p1, 'paren', inner))
            i = j + 1
        else:
            # 表达式块：读到下一个 < > 或 ( 为止
            j = i
            while j < n and cipher[j] not in '<>(':
                j += 1
            expr = cipher[i:j]
            groups.append((p1, 'expr', expr))
            i = j

    return groups


def _compute_index(p1):
    """根据 < > 前缀计算净索引。"""
    idx = 0
    for c in p1:
        if c == '<':
            idx -= 1
        elif c == '>':
            idx += 1
    return idx


def _add_at(arr, idx, v):
    """把值 v 加到 arr[idx]，自动扩展数组长度。负索引忽略。"""
    if idx < 0:
        return
    while len(arr) <= idx:
        arr.append(0)
    arr[idx] += v


def s_calculate(value, key_map):
    """
    解析密文，返回码点数组。

    新规则：
    - 每组为 p1 + body
    - p1 是一串 < >，按 < 减 1、> 加 1 得到 net
    - 基准索引为 0，所以组目标位置 = net
    - body 为表达式：求值后加到 calc[net]
    - body 为 (inner)：递归解析 inner 得到子数组，
      从 net 开始逐位与父数组对齐相加
    - 允许任意深度嵌套
    """
    if not value:
        return []
    groups = _parse_groups(value)
    calc = []
    for p1, kind, body in groups:
        idx = _compute_index(p1)
        if kind == 'expr':
            v = evaluate_expression(body, key_map)
            _add_at(calc, idx, v)
        else:  # paren
            sub = s_calculate(body, key_map)
            for k, v in enumerate(sub):
                _add_at(calc, idx + k, v)
    return calc


# ============================================================
#                       加密端
# ============================================================

def _make_block(v, rev_map):
    """生成字符块，值之和恰为 v。均匀随机选值，块内字符打乱。"""
    if v <= 0:
        return ""
    values = list(rev_map.keys())
    parts = []
    remaining = v
    while remaining > 0:
        candidates = [x for x in values if x <= remaining]
        if not candidates:
            break
        chosen = random.choice(candidates)
        parts.append(random.choice(rev_map[chosen]))
        remaining -= chosen
    random.shuffle(parts)
    return ''.join(parts)


def _make_noise(rev_map, level):
    """生成不改变值的噪声后缀：+X-X 或 .X/X。"""
    if level <= 0 or not rev_map:
        return ""
    values = list(rev_map.keys())
    out = []
    for _ in range(random.randint(0, level * 2)):
        v = random.choice(values)
        ch = random.choice(rev_map[v])
        if random.random() < 0.5:
            out.append('+' + ch + '-' + ch)
        else:
            out.append('.' + ch + '/' + ch)
    return ''.join(out)


def _make_suffix(target, rev_map, noise_level=2):
    """
    生成求值为 target 的表达式（仅用 + - . /，因为 () 被重定义了）。
    target < 50      → block(target)
    target = B²      → block(B).block(B)
    target = A + B²  → block(B).block(B)+block(A)
    """
    if target <= 0:
        if 1 in rev_map:
            return random.choice(rev_map[1])
        return random.choice(list(rev_map.values())[0])

    if target < 50:
        expr = _make_block(target, rev_map)
    else:
        B = int(math.isqrt(target))
        A = target - B * B
        b_blk = _make_block(B, rev_map)
        if A == 0:
            expr = b_blk + '.' + b_blk
        else:
            expr = b_blk + '.' + b_blk + '+' + _make_block(A, rev_map)

    expr += _make_noise(rev_map, noise_level)
    return expr


def _make_offset(net):
    """
    生成净偏移为 net 的 < > 串。
    必须非空。使用最短必要形式。
    """
    if net > 0:
        base = ['>'] * (net + 1) + ['<']
    elif net < 0:
        base = ['<'] * (-net + 1) + ['>']
    else:
        base = ['<', '>']
    random.shuffle(base)
    return ''.join(base)


def _split_value(value, num_parts):
    """把正整数 value 随机拆成 num_parts 个正整数。"""
    if num_parts <= 1 or value <= 1:
        return [value]
    num_parts = min(num_parts, value)
    if num_parts == 1:
        return [value]
    cuts = sorted(random.sample(range(1, value), num_parts - 1))
    parts = []
    prev = 0
    for c in cuts:
        parts.append(c - prev)
        prev = c
    parts.append(value - prev)
    return parts


def s_encrypt(value, _random=5, iv=0, key_map=None,
              max_groups=3, paren_prob=0.5):
    """
    加密函数入口。

    :param value: 原文
    :param _random: 噪声强度
    :param iv: 密码表偏移
    :param key_map: 密码表
    :param max_groups: 每字符最多拆几组
    :param paren_prob: 每组用括号的概率
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
    for i, code in enumerate(ord_codes):
        num_groups = random.randint(1, max_groups)
        num_groups = min(num_groups, code)
        if num_groups < 1:
            num_groups = 1
        parts = _split_value(code, num_groups)

        for part in parts:
            expr = _make_suffix(part, rev_map, noise_level=_random)
            p1 = _make_offset(i)     # 基准 0，所以 net = i

            if random.random() < paren_prob:
                # 括号块：子密文解析为 [part]
                inner = _make_offset(0) + expr
                result.append(p1 + '(' + inner + ')')
            else:
                result.append(p1 + expr)

    return ''.join(result)


def s_decrypt(value, key_map=None, iv=0):
    """解密函数入口。"""
    if key_map is None:
        key_map = dict(default_key_map)
    else:
        key_map = dict(key_map)
    for k in list(key_map.keys()):
        key_map[k] = key_map[k] + iv

    calc = s_calculate(value, key_map)
    return "".join(chr(c) for c in calc if c > 0)


# ============================================================
#                       测试
# ============================================================
if __name__ == "__main__":
    import time
    print("52pj - Pumpkin888666  [括号重定义版]")

    # 1. 括号对齐测试
    print("\n== 括号对齐测试 ==")
    key_map = dict(default_key_map)
    # 构造：[1,2,3,4,5] 基础值，位置2处加 [8,7]
    test_cipher = "<>a" + ">b" + ">>c" + ">>>d" + ">>>>e" + ">>(<>h>g)"
    calc = s_calculate(test_cipher, key_map)
    print(f"  密文: {test_cipher}")
    print(f"  解析: {calc}")
    print(f"  期望: [1, 2, 11, 11, 5]")
    print(f"  通过: {calc == [1, 2, 11, 11, 5]}")

    # 2. 嵌套括号测试
    print("\n== 嵌套括号测试 ==")
    inner2 = "<>h"                        # 解析为 [8]
    inner1 = "<>(" + inner2 + ")>g"       # 解析为 [8,7]
    nested = ">>(" + inner1 + ")"         # 加到父数组位置2
    calc2 = s_calculate(nested, key_map)
    print(f"  密文: {nested}")
    print(f"  解析: {calc2}")
    print(f"  期望: [0, 0, 8, 7]")
    print(f"  通过: {calc2 == [0, 0, 8, 7]}")

    # 3. 端到端加密解密
    print("\n== 端到端测试 ==")
    for original in ["hello", "你好世界", "这是一段测试文本，包含中文和English。"]:
        t0 = time.time()
        encrypted = s_encrypt(original, _random=10, max_groups=3, paren_prob=0.5)
        t1 = time.time()
        decrypted = s_decrypt(encrypted)
        t2 = time.time()

        n_lt = encrypted.count('<')
        n_gt = encrypted.count('>')
        n_lp = encrypted.count('(')
        n_rp = encrypted.count(')')

        print(f"原文: {original}")
        print(f"密文: {encrypted}")
        print(f"解密: {decrypted}")
        print(f"成功: {decrypted == original}")
        print(f"密文长度: {len(encrypted)}  '<':{n_lt}  '>':{n_gt}  '(':{n_lp}  ')':{n_rp}")
        print(f"加密: {t1-t0:.4f}s  解密: {t2-t1:.4f}s")
        print("-" * 60)