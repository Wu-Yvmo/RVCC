def align2(x: int, align: int) -> int:
    if x == 0:
        return 0
    if align == 0:
        raise Exception('')
    return (x + align - 1) // align * align

if __name__ == '__main__':
    print(align2(10, 16))