from typing import * # type: ignore
import os
import tqdm
test_items = [
    (r'{return 0;}', 0),
    (r'{return 42;}', 42),
    (r'{return 12-34+56}', 34),
    (r'{return  12 + 34 - 5 }', 41),
    (r'{return 5+6*7;}', 47),
    (r'{return 5*(9-6)}', 15),
    (r'{return 1-8/(2*2)+3*6;}', 17),
    (r'{return -10+20;}', 10),
    (r'{return - -10;}', 10),
    (r'{return - - +10;}', 10),
    (r'{return ------12*+++++----++++++++++4;}', 48),
    (r'{return 0==1;}', 0),
    (r'{return 42==42;}', 1),
    (r'{return 0!=1;}', 1),
    (r'{return 42!=42;}', 0),
    (r'{return 0<1;}', 1),
    (r'{return 1<1;}', 0),
    (r'{return 2<1;}', 0),
    (r'{return 0<=1;}', 1),
    (r'{return 1<=1;}', 1),
    (r'{return 2<=1;}', 0),
    (r'{return 1>0;}', 1),
    (r'{return 1>1;}', 0),
    (r'{return 1>2;}', 0),
    (r'{return 1>=0;}', 1),
    (r'{return 1>=1;}',1),
    (r'{return 1>=2;}', 0),
    (r'{return 5==2+3;}', 1),
    (r'{return 6==4+3;}', 0),
    (r'{return 0*9+5*2==4+4*(6/3)-2;}', 1),
    (r'{1; 2; return 3;}', 3),
    (r'{12+23;12+99/3; return 78-66;}', 12),
    (r'{int a=3; return a;}', 3),
    (r'{int a=3; return a;}', 3),
    (r'{int a=3; int z=5; return a+z;}', 8),
    (r'{int a, b; a=b=3; return a+b;}', 6),
    (r'{int a=3;int b=4;a=1; return a+b;}', 5),
    (r'{int foo=3; return foo;}', 3),
    (r'{int foo2=70; int bar4=4; return foo2+bar4;}', 74),
]

# [10] 支持单字母变量
# assert 3 'a=3; a;'
# assert 8 'a=3; z=5; a+z;'
# assert 6 'a=b=3; a+b;'
# assert 5 'a=3;b=4;a=1;a+b;'

# [11] 支持多字母变量
# assert 3 'foo=3; foo;'
# assert 74 'foo2=70; bar4=4; foo2+bar4;'
# assert 3 '1; 2; 3;'
# assert 12 '12+23;12+99/3;78-66;'
# # assert 期待值 输入值
# # [1] 返回指定数值
# assert 0 0
# assert 42 42

# # [2] 支持+ -运算符
# assert 34 '12-34+56'

# # [3] 支持空格
# assert 41 ' 12 + 34 - 5 '

# # [5] 支持* / ()运算符
# assert 47 '5+6*7'
# assert 15 '5*(9-6)'
# assert 17 '1-8/(2*2)+3*6'

# # [6] 支持一元运算的+ -
# assert 10 '-10+20'
# assert 10 '- -10'
# assert 10 '- - +10'
# assert 48 '------12*+++++----++++++++++4'

# # [7] 支持条件运算符
# assert 0 '0==1'
# assert 1 '42==42'
# assert 1 '0!=1'
# assert 0 '42!=42'

# assert 1 '0<1'

# assert 0 '1<1'

# assert 0 '2<1'
# assert 1 '0<=1'

# assert 1 '1<=1'
# assert 0 '2<=1'

# assert 1 '1>0'
# assert 0 '1>1'

# assert 0 '1>2'
# assert 1 '1>=0'

# assert 1 '1>=1'
# assert 0 '1>=2'
# assert 1 '5==2+3'
# assert 0 '6==4+3'
# assert 1 '0*9+5*2==4+4*(6/3)-2'

def assert_zero(to_assert: int):
    if to_assert != 0:
        raise Exception("Assertion failed")

def test(to_test: str, correct_ret: int):
    os.system(f"python3 main.py '{to_test}' > a.s")
    os.system("gcc a.s -o a.out")
    ret = os.system("./a.out") >> 8
    if ret != correct_ret:
        raise Exception(f'test {to_test} failed, get value {ret}, should get {correct_ret}')

if __name__ == '__main__':
    for test_item in tqdm.tqdm(test_items):
        test(test_item[0], test_item[1])
    print("Hello")