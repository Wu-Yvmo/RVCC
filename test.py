from typing import * # type: ignore
import os
import tqdm

test_items = [
    (r'int main() {return 0;}', 0),
    (r'int main() {return 42;}', 42),
    (r'int main() {return 12-34+56}', 34),
    (r'int main() {return  12 + 34 - 5 }', 41),
    (r'int main() {return 5+6*7;}', 47),
    (r'int main() {return 5*(9-6);}', 15),
    (r'int main() {return 1-8/(2*2)+3*6;}', 17),
    (r'int main() {return -10+20;}', 10),
    (r'int main() {return - -10;}', 10),
    (r'int main() {return - - +10;}', 10),
    (r'int main() {return ------12*+++++----++++++++++4;}', 48),
    (r'int main() {return 0==1;}', 0),
    (r'int main() {return 42==42;}', 1),
    (r'int main() {return 0!=1;}', 1),
    (r'int main() {return 42!=42;}', 0),
    (r'int main() {return 0<1;}', 1),
    (r'int main() {return 1<1;}', 0),
    (r'int main() {return 2<1;}', 0),
    (r'int main() {return 0<=1;}', 1),
    (r'int main() {return 1<=1;}', 1),
    (r'int main() {return 2<=1;}', 0),
    (r'int main() {return 1>0;}', 1),
    (r'int main() {return 1>1;}', 0),
    (r'int main() {return 1>2;}', 0),
    (r'int main() {return 1>=0;}', 1),
    (r'int main() {return 1>=1;}',1),
    (r'int main() {return 1>=2;}', 0),
    (r'int main() {return 5==2+3;}', 1),
    (r'int main() {return 6==4+3;}', 0),
    (r'int main() {return 0*9+5*2==4+4*(6/3)-2;}', 1),
    (r'int main() {1; 2; return 3;}', 3),
    (r'int main() {12+23;12+99/3; return 78-66;}', 12),
    (r'int main() {int a=3; return a;}', 3),
    (r'int main() {int a=3; return a;}', 3),
    (r'int main() {int a=3; int z=5; return a+z;}', 8),
    (r'int main() {int a, b; a=b=3; return a+b;}', 6),
    (r'int main() {int a=3;int b=4;a=1; return a+b;}', 5),
    (r'int main() {int foo=3; return foo;}', 3),
    (r'int main() {int foo2=70; int bar4=4; return foo2+bar4;}', 74),
    (r'int main() { return 1; 2; 3; }', 1),
    (r'int main() { 1; return 2; 3; }', 2),
    (r'int main() { 1; 2; return 3; }', 3),
    (r'int main() { {1; {2;} return 3;} }', 3),
    (r'int main() { ;;; return 5; }', 5),
    (r'int main() { if (0) return 2; return 3; }', 3),
    (r'int main() { if (1-1) return 2; return 3; }', 3),
    (r'int main() { if (1) return 2; return 3; }', 2),
    (r'int main() { if (2-1) return 2; return 3; }', 2),
    (r'int main() { if (0) { 1; 2; return 3; } else { return 4; } }', 4),
    (r'int main() { if (1) { 1; 2; return 3; } else { return 4; } }', 3),
    (r'int main() { int i=0; int j=0; for (i=0; i<=10; i=i+1) j=i+j; return j;}', 55),
    (r'int main() { for (;;) {return 3;} return 5; }', 3),
    (r'int main() { int i=0; while(i<10) { i=i+1; } return i;}', 10),
    (r'int main() { int x=3; return *&x; }', 3),
    # (r'{ int x=3; int y=&x; int z=&y; return **z; }', 3),
    (r'int main() { int x=3; int y=5; return *(&x+1); }', 5),
    (r'int main() { int x=3; int y=5; return *(&y-1); }', 3),
    # (r'{ int x=3; int y=&x; *y=5; return x; }', 5),
    (r'int main() { int x=3; int y=5; *(&x+1)=7; return y; }', 7),
    (r'int main() { int x=3; int y=5; *(&y-1)=7; return x; }', 7),
    (r'int main() { int x=3; int y=5; return *(&y-1); }', 3),
    (r'int main() { int x=3; int y=5; return *(&x+1); }', 5),
    (r'int main() { int x=3; int y=5; *(&y-1)=7; return x; }', 7),
    (r'int main() { int x=3; int y=5; *(&x+1)=7; return y; }', 7),
    (r'int ret3() {return 3; } int main() { return ret3(); }', 3),
    (r'int ret5() {return 5;} int main() { return ret5(); }', 5),
    (r'int ret3() {return 3; } int ret5() {return 5;} int main() { return ret3()+ret5(); }', 8),
    (r'int add(int a, int b) { return a+b;} int main() { return add(3, 5); }', 8),
    (r'int sub(int a, int b) {return 5-3;} int main() { return sub(5, 3); }', 2),
    (r'int add6(int a1, int a2, int a3, int a4, int a5, int a6) {return a1 + a2 + a3 + a4 + a5 + a6;} int main() { return add6(1,2,3,4,5,6); }', 21),
    (r'int add6(int a1, int a2, int a3, int a4, int a5, int a6) {return a1 + a2 + a3 + a4 + a5 + a6;} int main() { return add6(1,2,add6(3,4,5,6,7,8),9,10,11); }', 66),
    (r'int add6(int a1, int a2, int a3, int a4, int a5, int a6) {return a1 + a2 + a3 + a4 + a5 + a6;} int main() { return add6(1,2,add6(3,add6(4,5,6,7,8,9),10,11,12,13),14,15,16); }', 136),
    (r'int ret32() { return 32; } int main() { return ret32(); }', 32),
    (r'int main() { int x[2]; int *y=&x; *y=3; return *x; }', 3),
    (r'int main() { int x[3]; *x=3; *(x+1)=4; *(x+2)=5; return *x; }', 3),
    (r'int main() { int x[3]; *x=3; *(x+1)=4; *(x+2)=5; return *(x+1); }', 4),
    (r'int main() { int x[3]; *x=3; *(x+1)=4; *(x+2)=5; return *(x+2); }', 5),
    (r'int main() { int x[2][3]; int *y=x; *y=0; return **x; }', 0),
    (r'int main() { int x[2][3]; int *y=x; *(y+1)=1; return *(*x+1); }', 1),
    (r'int main() { int x[2][3]; int *y=x; *(y+2)=2; return *(*x+2); }', 2),
    (r'int main() { int x[2][3]; int *y=x; *(y+3)=3; return **(x+1); }', 3),
    (r'int main() { int x[2][3]; int *y=x; *(y+3)=4; return **(x+1); }', 4),
    (r'int main() { int x[2][3]; int *y=x; *(y+5)=5; return *(*(x+1)+2); }', 5),
    (r'int main() { int x[3]; *x=3; x[1]=4; x[2]=5; return *x; }', 3),
    (r'int main() { int x[3]; *x=3; x[1]=4; x[2]=5; return *(x+1); }', 4),
    (r'int main() { int x[3]; *x=3; x[1]=4; x[2]=5; return *(x+2); }', 5),
    (r'int main() { int x[3]; *x=3; x[1]=4; 2[x]=5; return *(x+2); }', 5),
    (r'int main() { int x[2][3]; int *y=x; y[0]=0; return x[0][0]; }', 0),
    (r'int main() { int x[2][3]; int *y=x; y[1]=1; return x[0][1]; }', 1),
    (r'int main() { int x[2][3]; int *y=x; y[2]=2; return x[0][2]; }', 2),
    (r'int main() { int x[2][3]; int *y=x; y[3]=3; return x[1][0]; }', 3),
    (r'int main() { int x[2][3]; int *y=x; y[4]=4; return x[1][1]; }', 4),
    (r'int main() { int x[2][3]; int *y=x; y[5]=5; return x[1][2]; }', 5),
    # (r'{}', -1),
    # (r'{}', -1),
]

test_items = test_items[::-1]

# [27] 支持一维数组
# assert 3 'int main() { int x[2]; int *y=&x; *y=3; return *x; }'
# assert 3 'int main() { int x[3]; *x=3; *(x+1)=4; *(x+2)=5; return *x; }'
# assert 4 'int main() { int x[3]; *x=3; *(x+1)=4; *(x+2)=5; return *(x+1); }'
# assert 5 'int main() { int x[3]; *x=3; *(x+1)=4; *(x+2)=5; return *(x+2); }'

# [28] 支持多维数组
# assert 0 'int main() { int x[2][3]; int *y=x; *y=0; return **x; }'
# assert 1 'int main() { int x[2][3]; int *y=x; *(y+1)=1; return *(*x+1); }'
# assert 2 'int main() { int x[2][3]; int *y=x; *(y+2)=2; return *(*x+2); }'
# assert 3 'int main() { int x[2][3]; int *y=x; *(y+3)=3; return **(x+1); }'
# assert 4 'int main() { int x[2][3]; int *y=x; *(y+4)=4; return *(*(x+1)+1); }'
# assert 5 'int main() { int x[2][3]; int *y=x; *(y+5)=5; return *(*(x+1)+2); }'

# # [29] 支持 [] 操作符
# assert 3 'int main() { int x[3]; *x=3; x[1]=4; x[2]=5; return *x; }'
# assert 4 'int main() { int x[3]; *x=3; x[1]=4; x[2]=5; return *(x+1); }'
# assert 5 'int main() { int x[3]; *x=3; x[1]=4; x[2]=5; return *(x+2); }'
# assert 5 'int main() { int x[3]; *x=3; x[1]=4; x[2]=5; return *(x+2); }'
# assert 5 'int main() { int x[3]; *x=3; x[1]=4; 2[x]=5; return *(x+2); }'

# assert 0 'int main() { int x[2][3]; int *y=x; y[0]=0; return x[0][0]; }'

# assert 1 'int main() { int x[2][3]; int *y=x; y[1]=1; return x[0][1]; }'
# assert 2 'int main() { int x[2][3]; int *y=x; y[2]=2; return x[0][2]; }'
# assert 3 'int main() { int x[2][3]; int *y=x; y[3]=3; return x[1][0]; }'
# assert 4 'int main() { int x[2][3]; int *y=x; y[4]=4; return x[1][1]; }'
# assert 5 'int main() { int x[2][3]; int *y=x; y[5]=5; return x[1][2]; }'




# [23] 支持零参函数调用
# assert 3 'int ret3() {return 3; } int main() { return ret3(); }'
# assert 5 'int ret5() {return 5;} int main() { return ret5(); }'
# assert 8 'int ret3() {return 3; } int ret5() {return 5;} int main() { return ret3()+ret5(); }'

# [24] 支持最多6个参数的函数调用
# assert 8 'int add(int a, int b) { return a+b;} int main() { return add(3, 5); }'
# assert 2 'int sub(int a, int b) {return 5-3;} int main() { return sub(5, 3); }'
# assert 21 'int add6(int a1, int a2, int a3, int a4, int a5, int a6) {return a1 + a2 + a3 + a4 + a5 + a6} int main() { return add6(1,2,3,4,5,6); }'
# assert 66 'int add6(int a1, int a2, int a3, int a4, int a5, int a6) {return a1 + a2 + a3 + a4 + a5 + a6} int main() { return add6(1,2,add6(3,4,5,6,7,8),9,10,11); }'
# assert 136 'int add6(int a1, int a2, int a3, int a4, int a5, int a6) {return a1 + a2 + a3 + a4 + a5 + a6} int main() { return add6(1,2,add6(3,add6(4,5,6,7,8,9),10,11,12,13),14,15,16); }'

# [25] 支持零参函数定义
# assert 32 'int ret32() { return 32; } int main() { return ret32(); }'

# [21] 支持指针的算术运算
# assert 3 '{ x=3; y=5; return *(&y-1); }'
# assert 5 '{ x=3; y=5; return *(&x+1); }'
# assert 7 '{ x=3; y=5; *(&y-1)=7; return x; }'
# assert 7 '{ x=3; y=5; *(&x+1)=7; return y; }'

# [20] 支持一元& *运算符
# assert 3 '{ x=3; return *&x; }'
# assert 3 '{ x=3; y=&x; z=&y; return **z; }'
# assert 5 '{ x=3; y=5; return *(&x+8); }'
# assert 3 '{ x=3; y=5; return *(&y-8); }'
# assert 5 '{ x=3; y=&x; *y=5; return x; }'
# assert 7 '{ x=3; y=5; *(&x+8)=7; return y; }'
# assert 7 '{ x=3; y=5; *(&y-8)=7; return x; }'

# [16] 支持for语句
# assert 55 '{ i=0; j=0; for (i=0; i<=10; i=i+1) j=i+j; return j; }'
# assert 3 '{ for (;;) {return 3;} return 5; }'

# [17] 支持while语句
# assert 10 '{ i=0; while(i<10) { i=i+1; } return i; }'

# [15] 支持if语句
# assert 3 '{ if (0) return 2; return 3; }'
# assert 3 '{ if (1-1) return 2; return 3; }'
# assert 2 '{ if (1) return 2; return 3; }'
# assert 2 '{ if (2-1) return 2; return 3; }'
# assert 4 '{ if (0) { 1; 2; return 3; } else { return 4; } }'
# assert 3 '{ if (1) { 1; 2; return 3; } else { return 4; } }'
# （没实现）

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

# [12] 支持return
# assert 1 '{ return 1; 2; 3; }'
# assert 2 '{ 1; return 2; 3; }'
# assert 3 '{ 1; 2; return 3; }'

# [13] 支持{...}
# assert 3 '{ {1; {2;} return 3;} }'

# [14] 支持空语句
# assert 5 '{ ;;; return 5; }'

def assert_zero(to_assert: int):
    if to_assert != 0:
        raise Exception("Assertion failed")

def test(to_test: str, correct_ret: int):
    os.system(f"python main.py '{to_test}' > a.s")
    os.system("riscv64-unknown-elf-gcc a.s -o a.out")
    ret = os.system("spike --isa=rv64gc pk a.out") >> 8
    if ret != correct_ret:
        raise Exception(f'test {to_test} failed, get value {ret}, should get {correct_ret}')

if __name__ == '__main__':
    for test_item in tqdm.tqdm(test_items):
        test(test_item[0], test_item[1])
    print("All test items has passed. Congratulatins, Sire!")