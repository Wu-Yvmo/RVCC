import ctypes

def align2(x: int, align: int) -> int:
    if x == 0:
        return 0
    if align == 0:
        raise Exception('')
    return (x + align - 1) // align * align

# 判断 32位表示整型够用
def i32_sufficient(x: int) -> int:
    return -2147483648 <= x <= 2147483647

# 对10进制字符求值
def __eval_dc(l: str) -> int:
    return ord(l) - ord('0')

# 对16进制字符串求值
def __eval_hc(l: str) -> int:
    lv = ord(l)
    if lv >= ord('0') and lv <= ord('9'):
        return lv - ord('0')
    if lv >= ord('a') and lv <= ord('f'):
        return lv - ord('a') + 10
    if lv >= ord('A') and lv <= ord('F'):
        return lv - ord('A') + 10
    raise Exception('')

def __eval_bc(l: str) -> int:
    return int(l == '1')

# 对8进制字符串求值
def __eval_oc(l: str) -> int:
    return __eval_dc(l)

def eval_i(l: str) -> int:
    '''
    # 描述
    对整型字面量进行求值
    '''
    # 16 进制
    # 这里实际上有bug.
    if l[0] == '0' and len(l) >= 2 and (l[1] == 'x' or l[1] == 'X'):
        lib = ctypes.CDLL('cdll/eval_i.so')
        eval_hex_i64 = lib.eval_hex_i64
        eval_hex_i64.argtypes = [ctypes.c_char_p]
        eval_hex_i64.restype = ctypes.c_long
        v = eval_hex_i64(l.encode())
        return v
    # 8 进制
    if l[0] == '0' and len(l) >= 2 and (l[1] == 'b' or l[1] == 'B'):
        v = 0
        l = l[2:]
        for c in l:
            v *= 2
            v += __eval_bc(c)
        return v
    # 8 进制
    if l[0] == '0':
        v = 0
        for c in l:
            v *= 8
            v += __eval_oc(c)
        return v
    # 10 进制
    v = 0
    for c in l:
        v *= 10
        v += __eval_dc(c)
    return v

if __name__ == '__main__':
    print(align2(10, 16))
    print(eval_i('0xffffffff'))
    print(2**32-1)
    lib = ctypes.CDLL('cdll/eval_i.so')
    hello = lib.hello
    hello()
    eval_hex_i64 = lib.eval_hex_i64
    eval_hex_i64.argtypes = [ctypes.c_char_p]
    eval_hex_i64.restype = ctypes.c_long
    print(eval_hex_i64(b'0xffffffff'))