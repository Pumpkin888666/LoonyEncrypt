"""
Title : loonyEncrypt - 神人加密
Description : 方案 C：解密端初始索引改为 0，<> 膨胀从 O(k²n²) 降到 O(kn²)。
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

OPERATORS = set("+-./()")


# ============================================================
#                       解密端（方案 C 修改）
# ============================================================

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
        index = 0   # ★ 方案 C：初始索引固定为 0（原版是 index = o）
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
    """生成不改变值的噪声后缀。用随机字符构造 +X-X 或 .X/X。"""
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
    生成求值为 target 的表达式。
    target < 50      → 普通块
    target = B²      → block(B).block(B)
    target = A + B²  → block(A)(block(B)
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
        if A == 0:
            b_blk = _make_block(B, rev_map)
            expr = b_blk + '.' + b_blk
        else:
            expr = _make_block(A, rev_map) + '(' + _make_block(B, rev_map)

    expr += _make_noise(rev_map, noise_level)
    return expr


def _make_offset(net):
    """
    生成只含 '<' 和 '>' 的字符串，净偏移 = count('>') - count('<') = net。
    必须同时包含至少一个 '<' 和一个 '>'。
    使用最短必要形式，不插入多余成对符号。
    """
    if net > 0:
        # net+1 个 '>' 和 1 个 '<'：净偏移 = (net+1) - 1 = net
        base = ['>'] * (net + 1) + ['<']
    elif net < 0:
        # |net|+1 个 '<' 和 1 个 '>'：净偏移 = 1 - (|net|+1) = net
        base = ['<'] * (-net + 1) + ['>']
    else:
        # 1 个 '>' 和 1 个 '<'：净偏移 = 0
        base = ['<', '>']
    random.shuffle(base)
    return ''.join(base)


def _split_value(value, num_parts):
    """把正整数 value 随机拆成 num_parts 个正整数。若 value 太小则自动减少份数。"""
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


def s_encrypt(value, _random=5, iv=0, key_map=None, max_groups=5):
    """
    加密函数入口（方案 C）

    :param value: 原文。string。
    :param _random: 每个表达式的噪声强度。int。
    :param iv: 密码表偏移量。int。
    :param key_map: 密码表。
    :param max_groups: 每个字符最多拆成多少组。调大→更乱但 <> 更多。
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

    groups = []

    for i, code in enumerate(ord_codes):
        # 每个字符拆 1 ~ max_groups 组
        num_groups = random.randint(1, max_groups)
        num_groups = min(num_groups, code)
        if num_groups < 1:
            num_groups = 1

        parts = _split_value(code, num_groups)

        for part in parts:
            # ★ 方案 C：初始索引为 0，所以净偏移 = 目标索引 i
            net = i
            p1 = _make_offset(net)
            p2 = _make_suffix(part, rev_map, noise_level=_random)
            groups.append(p1 + p2)

    return ''.join(groups)


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


# ============================================================
#                       测试
# ============================================================
if __name__ == "__main__":
    import time
    print("52pj - Pumpkin888666  [方案 C]")

    for original in ["hello", "你好世界", "这是一段测试文本，包含中文和English。"]:
        t0 = time.time()
        encrypted = s_encrypt(original, _random=10, max_groups=5)
        t1 = time.time()
        decrypted = s_decrypt(encrypted)
        t2 = time.time()

        n_lt = encrypted.count('<')
        n_gt = encrypted.count('>')
        n_groups = len(re.findall(r'[<>]+', encrypted))

        print(f"原文: {original}")
        print(f"密文: {encrypted}")
        print(f"解密: {decrypted}")
        print(f"成功: {decrypted == original}")
        print(f"组数: {n_groups}   原文长度: {len(original)}")
        print(f"密文总长: {len(encrypted)}   '<': {n_lt}   '>': {n_gt}   <>总数: {n_lt + n_gt}")
        print(f"加密: {t1-t0:.4f}s  解密: {t2-t1:.4f}s")
        print("-" * 60)