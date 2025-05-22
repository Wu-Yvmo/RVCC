import enum

class RegNo(enum.IntEnum):
    A0 = enum.auto()
    A1 = enum.auto()
    A2 = enum.auto()
    A3 = enum.auto()
    A4 = enum.auto()
    A5 = enum.auto()
    A6 = enum.auto()
    T0 = enum.auto()
    T1 = enum.auto()
    RA = enum.auto()
    FP = enum.auto()
    SP = enum.auto()

class Register:
    def __init__(self, no: RegNo):
        super().__init__()
        self.no = no

# IR是通用中间表达
class IR:
    def __init__(self):
        super().__init__()

# 标签，name是标签名
class Label(IR):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

# 预编译指令
class PreOrder(IR):
    def __init__(self, order: str, content: str):
        super().__init__()
        self.order = order
        self.content = content

# 指令
class Instruction(IR):
    def __init__(self):
        super().__init__()

# 加载立即数
class LI(Instruction):
    def __init__(self, dest: Register, value: str):
        super().__init__()
        self.dest = dest
        self.value = value

# 返回
class RET(Instruction):
    def __init__(self):
        super().__init__()

# 无条件跳转
class J(Instruction):
    def __init__(self, dest: str):
        super().__init__()
        self.dest = dest

# 有条件跳转 等于零则跳转
class BEQZ(Instruction):
    def __init__(self, src: Register, dest: str):
        super().__init__()
        self.src = src
        self.dest = dest

class CALL(Instruction):
    def __init__(self, dest: str):
        super().__init__()
        self.dest = dest

# 移动寄存器的值
class MV(Instruction):
    def __init__(self, dest: Register, src: Register):
        super().__init__()
        self.dest = dest
        self.src = src

# la
class LA(Instruction):
    def __init__(self, dest: Register, label: str):
        super().__init__()
        self.dest = dest
        self.label = label

# 指令+
class ADD(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 指令+的32位版本
class ADDW(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 指令+立即数版本
class ADDI(Instruction):
    def __init__(self, dest: Register, src1: Register, value: str):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.value = value

# 指令-
class SUB(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 指令-的32位版本
class SUBW(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 求反
class NEG(Instruction):
    def __init__(self, dest: Register, src: Register):
        super().__init__()
        self.dest = dest
        self.src = src

# 求反32位版本
class NEGW(Instruction):
    def __init__(self, dest: Register, src: Register):
        super().__init__()
        self.dest = dest
        self.src = src

# 指令*
class MUL(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 指令*的32位版本
class MULW(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 指令/
class DIV(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 指令/的32位版本
class DIVW(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 指令xor
class XOR(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 指令xori
class XORI(Instruction):
    def __init__(self, dest: Register, src: Register, value: str):
        super().__init__()
        self.dest = dest
        self.src = src
        self.value = value

# 逻辑左移-立即数版本
class SLLI(Instruction):
    def __init__(self, dest: Register, src: Register, value: str):
        super().__init__()
        self.dest = dest
        self.src = src
        self.value = value

# 算数右移-立即数版本
class SRAI(Instruction):
    def __init__(self, dest: Register, src: Register, value: str):
        super().__init__()
        self.dest = dest
        self.src = src
        self.value = value

# 逻辑右移（暂时没有提供支持）

# 指令seqz
class SEQZ(Instruction):
    def __init__(self, dest: Register, src: Register):
        super().__init__()
        self.dest = dest
        self.src = src

# 指令snez
class SNEZ(Instruction):
    def __init__(self, dest: Register, src: Register):
        super().__init__()
        self.dest = dest
        self.src = src

# 指令slt
class SLT(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 存储双字
class SD(Instruction):
    def __init__(self, src: Register, offset: str, base: Register):
        super().__init__()
        self.src = src
        self.offset = offset
        self.base = base

class SW(Instruction):
    def __init__(self, src: Register, offset: str, base: Register):
        super().__init__()
        self.src = src
        self.offset = offset
        self.base = base

# 存储字节
class SB(Instruction):
    def __init__(self, src: Register, offset: str, base: Register):
        super().__init__()
        self.src = src
        self.offset = offset
        self.base = base

# 加载双字
class LD(Instruction):
    def __init__(self, dest: Register, offset: str, base: Register):
        super().__init__()
        self.dest = dest
        self.offset = offset
        self.base = base

# 加载字
class LW(Instruction):
    def __init__(self, dest: Register, offset: str, base: Register):
        super().__init__()
        self.dest = dest
        self.offset = offset
        self.base = base

# 加载字节
class LB(Instruction):
    def __init__(self, dest: Register, offset: str, base: Register):
        super().__init__()
        self.dest = dest
        self.offset = offset
        self.base = base

if __name__ == '__main__':
    print('Hello, world')
    a: list[IR] = [Label('a')]
    a.append(PreOrder('order', 'content'))
    print(a)