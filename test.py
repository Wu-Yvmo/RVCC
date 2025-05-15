from typing import * # type: ignore
import os

test_items: list[str] = [
    'arith',
    'control',
    'function',
    'pointer',
    'string',
    'variables',
    'struct'
]

test_items = test_items[::-1]

# 也就是说 我们现在要大规模重构整个测试item了

def assert_zero(to_assert: int):
    if to_assert != 0:
        raise Exception("Assertion failed")

def run_tests():
    for test_item in test_items:
        run_test(test_item)
    
def run_test(test_item: str):
    # 执行编译工作
    if os.system(f'riscv64-unknown-elf-gcc -E -P -C test/{test_item}.c -o test/{test_item}.after.c'):
        raise Exception('pre expand error')
    if os.system(f'python main.py test/{test_item}.after.c -o test/{test_item}.after.s'):
        raise Exception('rvcc compile error')
    if os.system(f'riscv64-unknown-elf-gcc test/{test_item}.after.s test/common.c -o test/{test_item}.after.out'):
        raise Exception('gcc link error')
    if os.system(f'spike --isa=rv64gc pk test/{test_item}.after.out'):
        raise Exception('test error')
    # 清理中间产生的额外文件
    os.remove(f'test/{test_item}.after.c')
    os.remove(f'test/{test_item}.after.s')
    os.remove(f'test/{test_item}.after.out')

if __name__ == '__main__':
    run_tests()
    print("All test items has passed. Congratulatins, Sire!")