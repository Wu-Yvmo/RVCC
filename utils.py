def align2(x: int, align: int) -> int:
    if x == 0:
        return 0
    if align == 0:
        raise Exception('')
    return (x + align - 1) // align * align

# 判断 32位表示整型够用
def i32_sufficient(x: int) -> int:
    return -2147483648 <= x <= 2147483647

if __name__ == '__main__':
    print(align2(10, 16))